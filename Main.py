import requests
from bs4 import BeautifulSoup


def check_Price(url, target_price):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url,headers=headers)
        soup = BeautifulSoup(response.content,"html.parser")

        title = soup.find(id="productTitle").get_text().strip()
        price_str = soup.find(class_="a-Price-whole").get_text()

        
        current_price = float(price_str.replace(' ', '').replace('.',""))

        print(f"Product: {title[:50]}..")
        print(f"Current Price : {current_price}")

        if current_price <= target_price:
            print("Price has dropped! Consider purchasing.")
        else:
            print(f"Price is still high. target is {target_price}")

    except Exception as e:
        print(f"An error occurred: {e}")
 


# examples 
product_url = "https://www.alibaba.com/product-detail/Custom-Logo-Reusable-35mm-Film-Camera_1601437799832.html?spm=a2700.galleryofferlist.p_offer.d_image.3f1813a0iN0qcj&priceId=fa3d32d9165b46d89b818c4b174e8b62" # Should be replaced with actual product URL
check_Price(product_url, target_price=400)
