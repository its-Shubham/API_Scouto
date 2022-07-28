from flask import Flask, jsonify
import pymongo
from datetime import date, datetime as dt


app = Flask(__name__)


@app.route('/')
def hello_world():
    instruction={0:"Enter the Api as mentioned below :",
                1:"Enter name of book: example --> bookName/Watchmen",
                2:"Enter price: example --> priceRange/10",
                3:"Enter category + name/term + rent per day(range): example --> match/comic+Watch+8-10",
                4:"Enter book name + person name + issue date (BOOK IS ISSUED)/return date (BOOK IS RETURNED): example -->update/1984+shubham+2022/07/29(issue)",
                5:"enter name of book: example -->bookToPeople/the",
                6:"enter name of book: exapmle -->bookRent/Watchmen",
                7:"enter name of the person : example -->personBooks/<string:pname>",
                }    
    return instruction


@app.route('/bookName/<string:bname>')
def bookName(bname):
    # bname = input("enter name of book: ")
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["BOOKS"]
    collection = db["BookDetails"]
    books = collection.find({"book_name": {"$regex": f"{bname}", "$options": "i"}}, {
        "book_name": 1, "_id": 0})
    booklist = []
    for item in books:
        booklist.append(item)
    return jsonify(booklist)


@app.route('/priceRange/<int:price>')
def priceRange(price):
    # price = int(input("enter rate: "))
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["BOOKS"]
    collection = db["BookDetails"]
    books = collection.find({"rent_per_day": {"$lte": price}}, {
        "book_name": 1, "_id": 0})
    booklist = []
    for item in books:
        booklist.append(item)
    return jsonify(booklist)


@app.route('/match/<string:detail>')
def match(detail):
    # detail = input("enter category + name/term + rent per day(range): ")
    category, bname, price = detail.split("+")

    price1, price2 = price.split("-")
    price1 = int(price1)
    price2 = int(price2)

    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["BOOKS"]
    collection = db["BookDetails"]
    books = collection.find(
        {"book_name": {"$regex": f"{bname}", "$options": "i"}, "rent_per_day": {
            "$gte": price1, "$lte": price2}, "category": {"$regex": f"{category}", "$options": "i"}},
        {"_id": 0, "book_name": 1, "rent_per_day": 1, "category": 1})
    booklist = []
    for item in books:
        booklist.append(item)
    return jsonify(booklist)


@app.route('/update/<string:detail>')
def update(detail):
    # detail = input(
    #     "book name + person name + issue date -BOOK IS ISSUED-/return date -BOOK IS RETURNED-:")
    bname, pname, date = detail.split("+")
    date, use = date.split("-")
    dictdetails = {}

    client = pymongo.MongoClient("mongodb://localhost:27017")
    dbB = client["BOOKS"]
    collectionB = dbB["BookDetails"]

    # get all data from database BOOKS
    getdetails = collectionB.find({"book_name": {"$regex": f"{bname}", "$options": "i"}}, {
        "_id": 0, "book_name": 1, "rent_per_day": 1})
    for item in getdetails:
        dictdetails = item.copy()

    # get book name and rent par day
    bname1 = dictdetails["book_name"]
    rate = dictdetails["rent_per_day"]

    client = pymongo.MongoClient("mongodb://localhost:27017")
    dbT = client["TRANSACTIONS"]
    collectionT = dbT["TRANSACTIONS_DETAILS"]

    # validation
    if bname1 == bname:
        print("step 1")
        print(use)
        if ("ISSUE" in use) or ("issue" in use) or ("Issue" in use):
            print("entered in issue")
            issued = {
                "book_name": bname,
                "person_name": pname,
                "issue_date": date,
                "return_date": None
            }
            collectionT.insert_one(issued)
            print("issued successfully")
            return jsonify("issued successfully")
        elif ("RETURN" in use) or ("return" in use) or ("Return" in use):
            print("entered in return")
            collectionT.find_one_and_update(
                {"book_name": f"{bname}", "person_name": f"{pname}",
                    "issue_date": {"$ne": "null"}},
                {"$set": {"return_date": f"{date}"}})

            # rent calculation
            issuedate = ""
            for i in collectionT.find({"person_name": {"$regex": f"{pname}", "$options": "i"},
                                       "book_name": {"$regex": f"{bname}", "$options": "i"}}, {
                    "_id": 0, "issue_date": 1}):
                print("thi is I: ", i, "type of i:", type(i))
                issuedate = i["issue_date"]

            returndate = ""
            paymentDetails = collectionT.find({"person_name": {"$regex": f"{pname}", "$options": "i"},
                                               "book_name": {"$regex": f"{bname}", "$options": "i"}}, {
                "_id": 0, "return_date": 1})
            for j in paymentDetails:
                returndate = j["return_date"]

            res = (dt.strptime(f"{returndate}", "%Y/%m/%d") -
                   dt.strptime(f"{issuedate}", "%Y/%m/%d")).days
            print("rate-->", rate, "res-->", res)
            print("charges are :", rate * res)
            print("returned successfully")
            return jsonify(rate * res)
    else:
        return jsonify("Record Not Found")


@app.route('/bookToPeople/<string:bname>')
def bookToPeople(bname):
    try:
        # bname = input("enter name of book: ")
        client = pymongo.MongoClient("mongodb://localhost:27017")
        dbT = client["TRANSACTIONS"]
        collectionT = dbT["TRANSACTIONS_DETAILS"]
                
        
        count_people = collectionT.distinct("person_name",{"book_name": {"$regex": f"{bname}", "$options": "i"}})

        peoplename = collectionT.find(
            {"book_name": {"$regex": f"{bname}", "$options": "i"}, "issue_date": {"$ne": "null"}, "return_date": None},
            {"_id": 0, "person_name": 1})
        peoplelist=[]
        for items in peoplename:
            peoplelist.append(items)
            
        print("no. of people->",len(count_people),"name of people->",peoplelist)
        return jsonify(count_people, peoplelist)
    except Exception as e:
        return "error"
    


@app.route('/bookRent/<string:bname>')
def bookRent(bname):
    # bname = input("enter name of book: ")
    #To find rate of book from different database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    dbB = client["BOOKS"]
    collectionB = dbB["BookDetails"]

    #get all data from database BOOKS
    getdetails = collectionB.find({"book_name": {"$regex": f"{bname}", "$options": "i"}}, {
                                  "_id": 0, "rent_per_day": 1})
    for item in getdetails:
        dictdetails = item.copy()

    rate = dictdetails["rent_per_day"]
    print("Rate = ",rate)
    #To find no. of days
    client = pymongo.MongoClient("mongodb://localhost:27017")
    dbT = client["TRANSACTIONS"]
    collectionT = dbT["TRANSACTIONS_DETAILS"]
    days=collectionT.find({"book_name": {"$regex": f"{bname}", "$options": "i"}},
                          {"_id":0,"issue_date":1,"return_date":1})
    total_days=0
    for item in days:
        dif=0
        idate=item.get('issue_date')
        rdate=item.get('return_date')
        y1,m1,d1=idate.split("/")
        y2,m2,d2=rdate.split("/")
        d1=date(int(y1),int(m1),int(d1))
        d2=date(int(y2),int(m2),int(d2))
        dif=(d2-d1).days
        total_days+=dif
    print("cnt--->",total_days)
    
    print("Total Rent -->",rate*total_days)
    return jsonify(rate*total_days)
    

@app.route('/personBooks/<string:pname>')
def personBooks(pname):
    # pname = input("enter name of the person :")
    client = pymongo.MongoClient("mongodb://localhost:27017")
    dbT = client["TRANSACTIONS"]
    collectionT = dbT["TRANSACTIONS_DETAILS"]
    books = collectionT.distinct("book_name",{"person_name": {"$regex": f"{pname}", "$options": "i"}})
    return jsonify(books)


# def booksByDate():
#     dateRange = input("enter range of date in format year/month/start_date-year/month/end_date :")

#     client = pymongo.MongoClient("mongodb://localhost:27017")
#     dbT = client["TRANSACTIONS"]
#     collectionT = dbT["TRANSACTIONS_DETAILS"]
    
#     dateStart, dateEnd = dateRange.split('-')[0],dateRange.split('-')[1]  
#     booklist=[]
#     personlist=[]
#     dateStartPy = dt.strptime(dateStart, '%y/%m/%d')
#     dateEndPy = dt.strptime(dateEnd, '%y/%m/%d')
#     for 
#     datedata = collectionT.find("issue_date":"2022/07/22",)
    

if __name__ == "__main__":
    app.run(debug=True)
    
