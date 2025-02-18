from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

app = Flask(__name__)

playstore = playstore = pd.read_csv('data/googleplaystore.csv')

playstore = playstore.drop_duplicates(subset = 'App',keep='first')  

# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore = playstore.drop([10472])

playstore['Category'] = playstore['Category'].astype('category')
# Buang tanda koma(,) dan tambah(+) kemudian ubah tipe data menjadi integer
playstore['Installs'] = playstore['Installs'].apply(lambda x: x.replace(',',''))
playstore['Installs'] = playstore['Installs'].apply(lambda x: x.replace('+',''))

playstore['Installs'] = playstore['Installs'].astype('int')

# Bagian ini untuk merapikan kolom Size, Anda tidak perlu mengubah apapun di bagian ini
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

playstore['Price'] = playstore['Price'].apply(lambda x: x.replace('$',''))
playstore['Price'] = playstore['Price'].astype('float')

# Ubah tipe data Reviews, Size, Installs ke dalam tipe data integer
playstore[['Reviews','Size']]=playstore[['Reviews','Size']].astype('int')

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore.copy()
    plt.switch_backend('Agg') 
    # Statistik
    top_category=pd.crosstab(index=df2['Category'],
            columns='Jumlah',
            values=df2['App'],aggfunc='count').sort_values(by='Jumlah',ascending=False).reset_index()
    # Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        'most_categories' : top_category.nlargest(1, 'Jumlah').iloc[0]['Category'],
        'total': top_category.nlargest(1, 'Jumlah').iloc[0]['Jumlah'],
        'rev_table' : df2.sort_values(by='Reviews', ascending=False)[['Category', 'App', 'Reviews', 'Rating']].head(10).reset_index(drop=True).to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    ## Bar Plot
    cat_order = df2.groupby(by='Category').agg({'App': 'count'}).rename({'App': 'Total'}, axis=1).sort_values(by='Total', ascending=False).head()
    X = cat_order['Total']
    Y = cat_order.index
    my_colors = ['r','g','b','k','y','m','c']
    # bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    # bagian ini digunakan untuk membuat bar plot
    plt.barh(y=Y, width=X, color=my_colors)
    # bagian ini digunakan untuk menyimpan plot dalam format image.png
    plt.savefig('cat_order.png',bbox_inches="tight") 

    # bagian ini digunakan untuk mengconvert matplotlib png ke base64 agar dapat ditampilkan ke template html
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    # variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
    # halaman html
    result = str(figdata_png)[2:-1]
    
    ## Scatter Plot
    X = df2['Rating'].values # axis x
    Y = df2['Reviews'].values # axis y
    area = playstore['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    # isi nama method untuk scatter plot, variabel x, dan variabel y
    plt.scatter(x=Y,y=X, s=area, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('rev_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    ## Histogram Size Distribution
    X=(df2['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    ## Buatlah sebuah plot yang menampilkan insight di dalam data 
    df3=df2.copy()
    df3['Last Year Updated']=df3['Last Updated'].astype('datetime64[ns]').dt.year
    filtered_df3 = df3[df3['Type'] == 'Paid'] 
    Top_5_Application=filtered_df3.pivot_table(
    index='Last Year Updated',
    values='Installs',
    aggfunc='mean').sort_values(by='Last Year Updated', ascending=True)
    Top_5_Application.plot(kind='bar')
    plt.xlabel('Years')
    plt.ylabel('Avg Installs when Paid')
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1]

    # Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3, result4=result4)

if __name__ == "__main__": 
    app.run(debug=True)
