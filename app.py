from flask import Flask, request, render_template, redirect, url_for, jsonify, make_response, current_app
from pymongo import MongoClient
import requests
import hashlib
from datetime import datetime
from bson import ObjectId
import os
import jwt
import locale
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

# client = MongoClient('mongodb://localhost:27017')
client = MongoClient('mongodb://surya:surya@ac-q3ppb07-shard-00-00.ovgnl6x.mongodb.net:27017,ac-q3ppb07-shard-00-01.ovgnl6x.mongodb.net:27017,ac-q3ppb07-shard-00-02.ovgnl6x.mongodb.net:27017/?ssl=true&replicaSet=atlas-dd9kbd-shard-0&authSource=admin&retryWrites=true&w=majority')
db = client.wisatakita

app = Flask(__name__)

SECRET_KEY = 'secret1141'
TOKEN_KEY = 'mytoken'

locale.setlocale(locale.LC_ALL, 'id_ID')

@app.route('/', methods = ['GET'])
def main():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload =jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({"email": payload["id"]})
        is_admin = user_info.get("category") == "admin"
        logged_in = True
        print(user_info)
        return render_template('homepage.html', user_info=user_info, logged_in = logged_in, is_admin = is_admin)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem logging you in'
    return render_template('homepage.html', msg=msg)

@app.route('/signup')
def signup():
    return render_template('register.html')

@app.route('/sign_up/save', methods = ['POST'])
def sign_up():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    password_hash = hashlib.sha256(password. encode('utf-8')).hexdigest()
    doc = {
        "name" : name,
        "email" : email,
        "category" : 'visitor',
        "password" : password_hash                                          
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/signin')
def signin():
    return render_template('login.html')

@app.route('/sign_in', methods=['POST'])
def sign_in():
    email = request.form["email"]
    password = request.form["password"]
    print(email)
    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    print(pw_hash)
    result = db.users.find_one(
        {
            "email": email,
            "password": pw_hash,
        }
    )
    if result:
        payload = {
            "id": email,
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify(
            {
                "result": "success",
                "token": token,
            }
        )
    else:
        return jsonify(
            {
                "result": "fail",
                "msg": "We could not find a user with that id/password combination",
            }
        )

@app.route('/wisata', methods=['POST'])
def add_wisata():
    name = request.form.get('name')
    description = request.form.get('description')
    location = request.form.get('location')
    total_tickets = int(request.form.get('total_tickets'))
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
    file = request.files['image_wisata']
    extension = file.filename.split('.')[-1]
    filename = f'static/images/wisata-{name}-{mytime}.{extension}'
    file.save(filename)
    price = float(request.form.get('price'))
    formatted_price = locale.currency(price, grouping=True)
    db.wisata.insert_one({
        'name' : name,
        'description' : description,
        'location' : location,
        'price' : price,
        'price_rupiah' : formatted_price,
        'image_wisata' : filename,
        'total_tickets' : total_tickets,
        
    })
    return jsonify({'message': 'Sukses tambah wisata'}), 201

@app.route('/wisata', methods=['GET'])
def get_wisata():
    wisata = db.wisata.find()
    wisata_list = []
    for attraction in wisata:
        wisata_list.append({
            'id': str(attraction['_id']),
            'name': attraction['name'],
            'description': attraction['description'],
            'image_wisata' : attraction['image_wisata'],
            'total_tickets': attraction['total_tickets']
        })
    return jsonify(wisata_list), 200
@app.route('/wisata/<id>', methods=['PUT'])
def edit_wisata(id):
    name = request.form.get('name')
    description = request.form.get('description')
    location = request.form.get('location')
    total_tickets = int(request.form.get('total_tickets'))
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

    # Get data lama dari database
    existing_wisata = db.wisata.find_one({'_id': ObjectId(id)})
    if existing_wisata is None:
        return jsonify({'error': 'Wisata not found'}), 404

    # Handle upload file baru
    file = request.files.get('image_wisata')
    if file:
        # Hapus file lama jika file dirubah
        if 'image_wisata' in existing_wisata:
            existing_file_path = existing_wisata['image_wisata']
            if os.path.exists(existing_file_path):
                os.remove(existing_file_path)

        extension = file.filename.split('.')[-1]
        filename = f'static/images/wisata-{name}-{mytime}.{extension}'
        file.save(filename)
    else:
        # Menjaga file jika tidak ada file baru
        filename = existing_wisata.get('image_wisata')

    price = float(request.form.get('price'))
    formatted_price = locale.currency(price, grouping=True)

    # Update data database
    db.wisata.update_one(
        {'_id': ObjectId(id)},
        {
            '$set': {
                'name': name,
                'description': description,
                'location': location,
                'price': price,
                'price_rupiah' : formatted_price,
                'image_wisata': filename,
                'total_tickets': total_tickets
            }
        }
    )

    return jsonify({'message': 'Sukses edit wisata'}), 200

@app.route('/wisata/<post_id>', methods=['DELETE'])
def delete_wisata(post_id):
    existing_wisata = db.wisata.find_one({'_id': ObjectId(post_id)})
    existing_file_path = existing_wisata['image_wisata']
    os.remove(existing_file_path)
    result = db.wisata.delete_one({'_id': ObjectId(post_id)})    
    if result.deleted_count > 0:        
        return jsonify({'message': 'Post deleted successfully'}), 200
    else:
        return jsonify({'message': 'Post not found'}), 404
    
@app.route('/wisata/<wisata_id>', methods=['GET'])
def get_wisata_detail(wisata_id):
    attraction = db.wisata.find_one({'_id': ObjectId(wisata_id)})
    token_receive = request.cookies.get(TOKEN_KEY)
    logged_in = False
    try:
        payload =jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({"email": payload["id"]})
        is_admin = user_info.get("category") == "admin"
        logged_in = True
        if attraction:
            return render_template('detail wisata.html', attraction = attraction, user_info=user_info, logged_in = logged_in, is_admin = is_admin)
        else:
            return render_template('detail wisata.html', user_info=user_info, logged_in = logged_in)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem logging you in'
    return render_template('detail wisata.html', attraction = attraction, msg=msg)
    

@app.route('/wisata/book', methods=['POST'])
def book_ticket():
    attraction_id = request.form.get('attraction_id')
    num_tickets = int(request.form.get('num_tickets'))
    name = request.form.get('name')
    email = request.form.get('email')

    if not attraction_id or not num_tickets or not name or not email:
        return jsonify({'message': 'Attraction ID, number of tickets, visitor name, and visitor email are required'}), 400

    # Check ketersediaan wisata
    attraction = db.wisata.find_one({'_id': ObjectId(attraction_id)})
    wisata = attraction['name']
    location = attraction['location']
    if not attraction:
        return jsonify({'message': 'Attraction not found'}), 404

    # Check ketersediaan tiket
    total_tickets = attraction.get('total_tickets', 0)
    if num_tickets > total_tickets:
        return jsonify({'message': 'Not enough available tickets'}), 400

    # Update sisa tiket setelah di booking
    updated_tickets = total_tickets - num_tickets
    db.wisata.update_one({'_id': ObjectId(attraction_id)}, {'$set': {'total_tickets': updated_tickets}})

    price = attraction.get('price', 0)
    total_price = price * num_tickets
    formatted_price = locale.currency(total_price, grouping=True)

    # Record data booking tiket pengunjung
    db.bookings.insert_one({
        'attraction_id': attraction_id,
        'location': location,
        'wisata' : wisata,
        'num_tickets': num_tickets,
        'name': name,
        'email': email,
        'total_price' : formatted_price,
        'status' : 'Pending'
    })

    return jsonify({'message': 'Ticket booked successfully'}), 200

@app.route('/wisata/bookings', methods=['GET'])
def get_bookings():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload =jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({"email": payload["id"]})
        is_admin = user_info.get("category") == "admin"
        bookings = db.bookings.find()
        logged_in = True
        print(user_info)
        return render_template('cek booking.html', user_info=user_info, logged_in = logged_in, is_admin = is_admin, bookings = bookings)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem logging you in'
    return render_template('login.html', msg=msg)

@app.route('/wisata/bookings/<booking_id>', methods=['PUT'])
def update_booking_status(booking_id):
    new_status = request.form.get('status')

    if not new_status:
        return jsonify({'message': 'New status is required'}), 400

    # Check if the booking exists
    booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    # Update the booking status
    db.bookings.update_one({'_id': ObjectId(booking_id)}, {'$set': {'status': new_status}})

    return jsonify({'message': 'Booking status updated successfully'}), 200

@app.route('/generate_pdf/<booking_id>')
def generate_pdf(booking_id):
    specific_card = db.bookings.find_one({'_id': ObjectId(booking_id)})

    # Buat buffer penyimpan pdf
    buffer = io.BytesIO()

    # Buat canvas pdf
    pdf = canvas.Canvas(buffer)

    # Styling content
    font_bold = 'Helvetica-Bold'
    font_normal = 'Helvetica'
    font_color = 'black'
    font_size = 12
    underline = True
    border = True

    # Atur styling
    pdf.setFont(font_bold, font_size)
    pdf.setFillColor(font_color)

    if underline:
        pdf.setStrokeColor(font_color)
        pdf.setLineWidth(0.5)
        pdf.line(100, 795, 400, 795)  # Add an underline

    if border:
        pdf.setStrokeColor(font_color)
        pdf.setLineWidth(1)
        pdf.rect(100, 780, 400, 50)  # Add a border

    # Draw text
    pdf.drawString(100, 800, "WisataKita | Bukti Booking Tiket")
    pdf.setFont(font_normal, font_size)
    pdf.drawString(100, 760, f"a.n. {specific_card['name']}")
    pdf.drawString(100, 740, f"{specific_card['status']}")
    pdf.drawString(100, 720, f"{specific_card['wisata']}")
    pdf.drawString(100, 700, f"{specific_card['location']}")
    pdf.drawString(100, 680, f"Jumlah tiket {specific_card['num_tickets']}")
    pdf.drawString(100, 500, f"Dibayar lunas sejumlah {specific_card['total_price']}")

    # Cap tiket
    image_filename = "Cap.png"  # Replace with the actual image filename
    image_path = current_app.root_path + '/static/' + image_filename
    image = ImageReader(image_path)

    image_x = 100
    image_y = 640
    pdf.drawImage(image, image_x, image_y, 117, 50)

    # Save PDF Content
    pdf.save()

    # Rewind the buffer and create a response object
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers.set('Content-Disposition', 'attachment', filename=f"{specific_card['name']} Tiket {specific_card['wisata']}.pdf")
    response.headers.set('Content-Type', 'application/pdf')
    return response

@app.route('/discover', methods = ['GET'])
def discover():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload =jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({"email": payload["id"]})
        is_admin = user_info.get("category") == "admin"
        logged_in = True
        print(user_info)
        return render_template('discover.html', user_info=user_info, logged_in = logged_in, is_admin = is_admin)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem logging you in'
    return render_template('discover.html', msg=msg)

@app.route('/cekpesanan/<name>', methods = ['GET'])
def cekpesan(name):
    token_receive = request.cookies.get(TOKEN_KEY)
    if not token_receive:
        return redirect('/forbidden')
    try:
        payload =jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({"email": payload["id"]})
        if not user_info:
            return redirect('/forbidden')
        logged_in = True
        if user_info['name'] != name:
            return redirect('/forbidden')
        bookings = db.bookings.find({'name' : name})
        listbooking = []

        for booking in bookings:
            listbooking.append({
                'id': str(booking['_id']),
                'wisata': booking['wisata'],
                'num_tickets': booking['num_tickets'],
                'status' : booking['status'],
                'total_price' : booking['total_price']
            })
        return render_template('cek pesanan.html', user_info=user_info, logged_in = logged_in, listbooking = listbooking)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem logging you in'
    return render_template('cek pesanan.html', msg=msg)

@app.route('/forbidden', methods = ['GET'])
def error():
    return render_template('error.html')

@app.route('/search', methods = ['GET'])
def search():
    query_params = request.args
    search_query = query_params.get('q', '')

    wisata = db.wisata.find({'name': {'$regex': search_query, '$options': 'i'}})

    wisata_list = []
    for attraction in wisata:
        wisata_list.append({
            'id': str(attraction['_id']),
            'name': attraction['name'],
            'description': attraction['description'],
            'image_wisata' : attraction['image_wisata'],
            'total_tickets': attraction['total_tickets']
        })

    return jsonify(wisata_list), 200
    



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)