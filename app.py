from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, session
from flask_sqlalchemy import SQLAlchemy
import json
import os
from datetime import datetime
import csv
from flask import Response, request
from flask import make_response
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import io
import logging
from flask_mail import Mail, Message



app = Flask(__name__)
app.secret_key = "your_secret_key"

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'steven4244@gmail.com'  # Replace with your email address
app.config['MAIL_PASSWORD'] = 'uuvo dcfb gncl xqgl'  # Replace with your email password or app-specific password
app.config['MAIL_DEFAULT_SENDER'] = 'steven4244@gmail.com'  # Default sender email address

mail = Mail(app)

@app.route('/submit_ticket', methods=['POST'])
def submit_ticket():
    try:
        data = request.form
        subject = data.get('subject')
        description = data.get('description')
        user_email = data.get('email', 'No email provided')

        if not subject or not description:
            return jsonify({'success': False, 'message': 'Subject and description are required'}), 400

        # Send email to yourself
        msg = Message(
            subject=f"New Service Ticket: {subject}",
            recipients=["steven4244@gmail.com"],  # Replace with your email
            body=f"Description:\n{description}\n\nSubmitted by: {user_email}"
        )
        mail.send(msg)

        return jsonify({'success': True, 'message': 'Ticket submitted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Read the environment variables securely
db_user = os.getenv('DB_USER')  # Your database username
db_password = os.getenv('DB_PASSWORD')  # Your database password
db_host = os.getenv('DB_HOST')  # Your database host
db_port = os.getenv('DB_PORT')  # Your database port
db_name = os.getenv('DB_NAME')  # Your database name
db_sslmode = os.getenv('DB_SSLMODE')  # SSL Mode (e.g., "required" or "verify-full")
db_ssl_ca = os.getenv('DB_SSL_CA')  # Path to CA certificate (e.g., "/path/to/ca-certificate.pem")
db_ssl_cert = os.getenv('DB_SSL_CERT')  # Path to client certificate (optional)
db_ssl_key = os.getenv('DB_SSL_KEY')  # Path to client key (optional)

# Construct the SQLAlchemy database URI using the environment variables
sqlalchemy_uri = (
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
)

# Add SSL parameters if available
if db_sslmode == "required" or db_sslmode == "verify-full":
    sqlalchemy_uri += f"?ssl_ca={db_ssl_ca}"
    if db_ssl_cert:
        sqlalchemy_uri += f"&ssl_cert={db_ssl_cert}"
    if db_ssl_key:
        sqlalchemy_uri += f"&ssl_key={db_ssl_key}"

# Set the SQLAlchemy URI in the Flask app
app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

# Initialize the SQLAlchemy instance
db = SQLAlchemy(app)




TURN_OPTIONS = ["left", "right", "supine", "chair", "nurse", "refused", "out of room"]
DAY_HOURS = ["7am", "9am", "11am", "1pm", "3pm", "5pm"]
NIGHT_HOURS = ["7pm", "9pm", "11pm", "1am", "3am", "5am"]

ROOMS_FILE = os.path.join(os.path.dirname(__file__), "rooms_setup.json")

class TurnTracker(db.Model):
    __tablename__ = 'turn_tracker'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    datetime = db.Column(db.DateTime, nullable=False)  # Use a single datetime field
    unit = db.Column(db.String(50), nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    turn_status = db.Column(db.String(50), nullable=True)
    name1 = db.Column(db.String(50), nullable=True)
    name2 = db.Column(db.String(50), nullable=True)

USERS = {
    "admin": {"password": "adminpass", "role": "admin"},
    "staff": {"password": "staffpass", "role": "staff"},
}

def load_rooms():
    if os.path.exists(ROOMS_FILE):
        with open(ROOMS_FILE, "r") as file:
            all_rooms = json.load(file)
            return all_rooms  # Return as-is without appending "_inactive" tags
    return {}

def save_rooms(unit, rooms):
    all_rooms = load_rooms()
    all_rooms[unit] = rooms
    try:
        with open(ROOMS_FILE, "w") as file:
            json.dump(all_rooms, file)
    except Exception as e:
        print(f"Error saving rooms: {e}")

        from datetime import datetime, timedelta

def generate_night_shift_times(base_date):
    """
    Generate time slots for a night shift, spanning evening hours of base_date and morning hours of the next day.
    """
    evening_hours = [f"{base_date} {hour}" for hour in ["7pm", "9pm", "11pm"]]
    next_date = (datetime.strptime(base_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    morning_hours = [f"{next_date} {hour}" for hour in ["1am", "3am", "5am"]]
    return evening_hours + morning_hours


@app.route('/add_room', methods=['POST'])
def add_room():
    room = request.form.get('room')
    unit = request.form.get('unit')
    shift = request.form.get('shift')
    date = request.form.get('date')

    # Load the rooms data
    all_rooms = load_rooms()

    # Ensure the unit exists in the room data
    if unit not in all_rooms:
        all_rooms[unit] = []

    # Ensure inactive unit exists
    inactive_unit = f"{unit}_inactive"
    if inactive_unit not in all_rooms:
        all_rooms[inactive_unit] = []

    # Check if the room is in the inactive list
    if room in all_rooms[inactive_unit]:
        # Remove the room from the inactive rooms list
        all_rooms[inactive_unit].remove(room)

        # Add the room to the active rooms list
        all_rooms[unit].append(room)

        # Sort the rooms in both lists (active and inactive) by room number
        all_rooms[unit] = sorted(all_rooms[unit], key=lambda r: int(r.split(' ')[0]))
        all_rooms[inactive_unit] = sorted(all_rooms[inactive_unit], key=lambda r: int(r.split(' ')[0]))

        # Save the updated rooms data to the JSON file
        try:
            with open(ROOMS_FILE, 'w') as file:
                json.dump(all_rooms, file, indent=4)
            flash(f"Room {room} added successfully.", "success")
        except Exception as e:
            flash(f"Error adding room: {e}", "danger")
    else:
        flash(f"Room {room} not found in inactive rooms.", "warning")

    # Redirect back to the manage unit page
    return redirect(url_for('manage_unit', unit=unit, shift=shift, date=date))


@app.route('/delete_room', methods=['POST'])
def delete_room():
    data = request.get_json()
    app.logger.info(f"Delete request received: {data}")
    room = data.get('room')
    unit = data.get('unit')

    if not room or not unit:
        return jsonify({"success": False, "message": "Room or unit missing in request."}), 400

    try:
        all_rooms = load_rooms()
    except Exception as e:
        app.logger.error(f"Error loading rooms: {e}")
        return jsonify({"success": False, "message": "Error loading rooms."}), 500

    if unit in all_rooms:
        if room in all_rooms[unit]:
            try:
                all_rooms[unit].remove(room)
                inactive_unit = f"{unit}_inactive"
                if inactive_unit not in all_rooms:
                    all_rooms[inactive_unit] = []
                all_rooms[inactive_unit].append(room)
                all_rooms[unit] = sorted(all_rooms[unit], key=lambda r: int(r.split(' ')[0]))
                all_rooms[inactive_unit] = sorted(all_rooms[inactive_unit], key=lambda r: int(r.split(' ')[0]))
                with open(ROOMS_FILE, 'w') as file:
                    json.dump(all_rooms, file, indent=4)
                return jsonify({"success": True, "message": f"Room {room} successfully moved to inactive."})
            except Exception as e:
                return jsonify({"success": False, "message": f"Error updating rooms: {e}"}), 500
        else:
            return jsonify({"success": False, "message": f"Room {room} not found in active rooms."}), 404
    return jsonify({"success": False, "message": "Unit not found."}), 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate user
        user = USERS.get(username)
        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            flash('Login successful', 'success')
            return redirect(url_for('index'))  # Redirect to the index page
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear the session data
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))  # Redirect to the login page


@app.route('/admin')
def admin_index():
    if 'username' not in session or session['role'] != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))
    return render_template('admin_index.html')

@app.route('/staff')
def staff_index():
    if 'username' not in session or session['role'] != 'staff':
        flash('Access denied. Staff only.', 'danger')
        return redirect(url_for('login'))
    return render_template('staff_index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please log in to access the dashboard', 'danger')
        return redirect(url_for('login'))
    
    # Render a different view for admin and staff
    if session['role'] == 'admin':
        return "Welcome Admin! <a href='/logout'>Logout</a>"
    elif session['role'] == 'staff':
        return "Welcome Staff! <a href='/logout'>Logout</a>"
    
@app.route("/api/units", methods=["GET"])
def get_units():
    all_rooms = load_rooms()
    # Filter out inactive units
    unit_names = [unit for unit in all_rooms.keys() if not unit.endswith("_inactive")]
    return jsonify({"units": unit_names})

@app.route('/api/rooms', methods=['GET'])
def get_rooms_for_unit():
    unit = request.args.get('unit')
    if not unit:
        return jsonify({"error": "Unit is required"}), 400

    # Load room data
    all_rooms = load_rooms()

    # Get active and inactive rooms for the selected unit
    active_rooms = all_rooms.get(unit, [])
    inactive_rooms = all_rooms.get(f"{unit}_inactive", [])

    # Combine active and inactive rooms without tags
    rooms = active_rooms + inactive_rooms

    if not rooms:
        return jsonify({"error": "No rooms found for this unit"}), 404

    return jsonify({"rooms": rooms}), 200

@app.route('/')
def index():
    if 'username' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_index'))
        elif session['role'] == 'staff':
            return redirect(url_for('staff_index'))
    else:
        return redirect(url_for('login'))

@app.route("/", methods=["POST"])
def start_turn_team():
    unit = request.form.get("unit")
    shift = request.form.get("shift")
    date = request.form.get("date")

    if not unit or not shift or not date:
        flash("All fields are required.", "danger")
        return redirect(url_for("index"))

    return redirect(url_for("manage_unit", unit=unit, shift=shift, date=date))

@app.route('/unit/<unit>', methods=['GET'])
def manage_unit(unit):
    shift = request.args.get('shift', 'Days')
    date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))

    # Parse the provided date
    base_date = datetime.strptime(date, '%Y-%m-%d')
    next_date = base_date + timedelta(days=1)

    # Generate full date-time headers
    if shift.lower() == 'nights':
        hours = [
            base_date.replace(hour=19).strftime('%Y-%m-%d %I:%M %p'),  # 7pm
            base_date.replace(hour=21).strftime('%Y-%m-%d %I:%M %p'),  # 9pm
            base_date.replace(hour=23).strftime('%Y-%m-%d %I:%M %p'),  # 11pm
            next_date.replace(hour=1).strftime('%Y-%m-%d %I:%M %p'),   # 1am
            next_date.replace(hour=3).strftime('%Y-%m-%d %I:%M %p'),   # 3am
            next_date.replace(hour=5).strftime('%Y-%m-%d %I:%M %p'),   # 5am
        ]
    else:
        hours = [
            base_date.replace(hour=7).strftime('%Y-%m-%d %I:%M %p'),   # 7am
            base_date.replace(hour=9).strftime('%Y-%m-%d %I:%M %p'),   # 9am
            base_date.replace(hour=11).strftime('%Y-%m-%d %I:%M %p'),  # 11am
            base_date.replace(hour=13).strftime('%Y-%m-%d %I:%M %p'),  # 1pm
            base_date.replace(hour=15).strftime('%Y-%m-%d %I:%M %p'),  # 3pm
            base_date.replace(hour=17).strftime('%Y-%m-%d %I:%M %p'),  # 5pm
        ]

    # Load rooms from JSON
    all_rooms = load_rooms()
    active_rooms = all_rooms.get(unit, [])
    inactive_rooms = all_rooms.get(f"{unit}_inactive", [])

    # Initialize room data and names
    room_data = {room: {hour: {"turn_status": "", "name1": "", "name2": ""} for hour in hours} for room in active_rooms}
    names = {hour: {"name1": "", "name2": ""} for hour in hours}  # Initialize names

    # Query existing turn data from the database (if any)
    entries = TurnTracker.query.filter(
        TurnTracker.unit == unit,
        TurnTracker.datetime >= datetime.strptime(hours[0], '%Y-%m-%d %I:%M %p'),
        TurnTracker.datetime <= datetime.strptime(hours[-1], '%Y-%m-%d %I:%M %p')
    ).all()

    # Populate room_data and names with database entries
    for entry in entries:
        room = entry.room_number
        hour_key = entry.datetime.strftime('%Y-%m-%d %I:%M %p')
        if room in room_data and hour_key in room_data[room]:
            room_data[room][hour_key] = {
                "turn_status": entry.turn_status or "",
                "name1": entry.name1 or "",
                "name2": entry.name2 or "",
            }
        if hour_key in names:
            names[hour_key] = {
                "name1": entry.name1 or "",
                "name2": entry.name2 or "",
            }

    return render_template(
        'manage_rooms.html',
        unit=unit,
        shift=shift,
        date=date,
        hours=hours,
        room_data=room_data,
        rooms=active_rooms,  # Pass active rooms from JSON
        inactive_rooms=inactive_rooms,  # Pass inactive rooms from JSON
        names=names,
        TURN_OPTIONS=TURN_OPTIONS
    )

@app.route('/save_turn_data', methods=['POST'])
def save_turn_data():
    unit = request.form.get('unit')
    shift = request.form.get('shift')
    date = request.form.get('date')
    selected_hour = request.form.get('selected_hour')

    if not selected_hour:
        flash("No hour selected. Please select an hour to save data.", "danger")
        return redirect(url_for('manage_unit', unit=unit, shift=shift, date=date))

    # Parse the base date and calculate the next day
    try:
        base_date = datetime.strptime(date, '%Y-%m-%d')
        next_date = base_date + timedelta(days=1)
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
        return redirect(url_for('manage_unit', unit=unit, shift=shift, date=date))

    # Map hours to datetime objects (ensure all displayed hours are included)
    hour_to_datetime = {}
    if shift.lower() == 'nights':
        hour_to_datetime = {
            base_date.replace(hour=19).strftime('%Y-%m-%d %I:%M %p'): base_date.replace(hour=19),  # 7pm
            base_date.replace(hour=21).strftime('%Y-%m-%d %I:%M %p'): base_date.replace(hour=21),  # 9pm
            base_date.replace(hour=23).strftime('%Y-%m-%d %I:%M %p'): base_date.replace(hour=23),  # 11pm
            next_date.replace(hour=1).strftime('%Y-%m-%d %I:%M %p'): next_date.replace(hour=1),    # 1am
            next_date.replace(hour=3).strftime('%Y-%m-%d %I:%M %p'): next_date.replace(hour=3),    # 3am
            next_date.replace(hour=5).strftime('%Y-%m-%d %I:%M %p'): next_date.replace(hour=5),    # 5am
        }
    else:
        hour_to_datetime = {
            base_date.replace(hour=7).strftime('%Y-%m-%d %I:%M %p'): base_date.replace(hour=7),   # 7am
            base_date.replace(hour=9).strftime('%Y-%m-%d %I:%M %p'): base_date.replace(hour=9),   # 9am
            base_date.replace(hour=11).strftime('%Y-%m-%d %I:%M %p'): base_date.replace(hour=11),  # 11am
            base_date.replace(hour=13).strftime('%Y-%m-%d %I:%M %p'): base_date.replace(hour=13),  # 1pm
            base_date.replace(hour=15).strftime('%Y-%m-%d %I:%M %p'): base_date.replace(hour=15),  # 3pm
            base_date.replace(hour=17).strftime('%Y-%m-%d %I:%M %p'): base_date.replace(hour=17),  # 5pm
        }

    # Ensure the selected hour exists in the mapping
    selected_datetime = hour_to_datetime.get(selected_hour)
    if not selected_datetime:
        flash(f"Invalid selected hour: {selected_hour}.", "danger")
        return redirect(url_for('manage_unit', unit=unit, shift=shift, date=date))

    # Process room data
    rooms = [key.split('_')[2] for key in request.form.keys() if key.startswith('turn_status_')]
    if not rooms:
        flash("No rooms found to save data for.", "warning")
        return redirect(url_for('manage_unit', unit=unit, shift=shift, date=date))

    # Save or update data for each room
    try:
        for room in rooms:
            turn_status = request.form.get(f'turn_status_{room}_{selected_hour}', '').strip()
            name1 = request.form.get(f'name1_{selected_hour}', '').strip()
            name2 = request.form.get(f'name2_{selected_hour}', '').strip()

            # Query for an existing entry
            entry = TurnTracker.query.filter_by(
                datetime=selected_datetime,
                unit=unit,
                room_number=room
            ).first()

            if entry:
                # Update existing entry
                entry.turn_status = turn_status
                entry.name1 = name1
                entry.name2 = name2
            else:
                # Add a new entry
                new_entry = TurnTracker(
                    datetime=selected_datetime,
                    unit=unit,
                    room_number=room,
                    turn_status=turn_status,
                    name1=name1,
                    name2=name2
                )
                db.session.add(new_entry)

        # Commit all changes to the database
        db.session.commit()
        # Format the datetime for the success message
        formatted_datetime = selected_datetime.strftime('%Y-%m-%d %I:%M %p')
        flash(f"Data saved successfully for {formatted_datetime}!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while saving data: {e}", "danger")

    return redirect(url_for('manage_unit', unit=unit, shift=shift, date=date))


@app.route('/export', methods=['GET'])
def export_data():
    unit = request.args.get('unit', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Validate and parse dates
    try:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1) if end_date else None
    except ValueError:
        flash("Invalid date format. Please ensure the dates are correct.", "danger")
        return redirect(url_for('admin_index'))

    # Build query with filters
    query = TurnTracker.query
    if unit:
        query = query.filter(TurnTracker.unit == unit)
    if start_datetime:
        query = query.filter(TurnTracker.datetime >= start_datetime)
    if end_datetime:
        query = query.filter(TurnTracker.datetime <= end_datetime)

    # Fetch data
    entries = query.order_by(TurnTracker.datetime.asc()).all()

    # Generate CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Time', 'Unit', 'Room', 'Turn Status', 'Name1', 'Name2'])

    for entry in entries:
        writer.writerow([
            entry.datetime.strftime('%Y-%m-%d'),
            entry.datetime.strftime('%I:%M %p'),
            entry.unit,
            entry.room_number,
            entry.turn_status or '',
            entry.name1 or '',
            entry.name2 or ''
        ])

    # Prepare response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=turn_data.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/export_filtered_turn_data', methods=['GET'])
def export_filtered_turn_data():
    # Retrieve filter parameters from the query string
    unit = request.args.get('unit')
    room = request.args.get('room')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Query the database based on the filters
    query = TurnTracker.query

    if unit:
        query = query.filter(TurnTracker.unit == unit)
    if room:
        query = query.filter(TurnTracker.room_number == room)
    if start_date:
        query = query.filter(TurnTracker.date >= start_date)
    if end_date:
        query = query.filter(TurnTracker.date <= end_date)

    # Fetch filtered data
    data = query.all()

    # Prepare CSV response
    def generate_csv():
        # Create the header row
        yield "Date,Unit,Room Number,Hour,Turn Status,Name1,Name2\n"
        
        # Loop through the data and write rows to the CSV
        for entry in data:
            yield f"{entry.date},{entry.unit},{entry.room_number},{entry.hour},{entry.turn_status},{entry.name1},{entry.name2}\n"

    # Return the response with CSV content
    return Response(
        generate_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=turn_tracker_export_{start_date}_to_{end_date}.csv"},
    )

@app.route('/export_turn_data_horizontal', methods=['GET'])
def export_turn_data_horizontal():
    unit = request.args.get('unit', None)
    room = request.args.get('room', None)
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)

    if not start_date or not end_date:
        flash("Start and End dates are required.", "danger")
        return redirect(url_for('view_turn_data_horizontal'))

    # Query data from database
    query = TurnTracker.query.filter(
        TurnTracker.date >= start_date,
        TurnTracker.date <= end_date
    )

    if unit:
        query = query.filter(TurnTracker.unit == unit)

    if room and room != "All Rooms":
        query = query.filter(TurnTracker.room_number == room)

    turn_data = query.order_by(TurnTracker.room_number, TurnTracker.date, TurnTracker.hour).all()

    # Create structured data for the table
    structured_data = {}
    all_dates_hours = set()
    for entry in turn_data:
        room = entry.room_number
        date_hour = f"{entry.date} {entry.hour}"
        all_dates_hours.add(date_hour)
        if room not in structured_data:
            structured_data[room] = {}
        structured_data[room][date_hour] = {
            "turn_status": entry.turn_status or "",
            "name1": entry.name1 or "",
            "name2": entry.name2 or ""
        }

    # Sort dates and hours
    sorted_dates_hours = sorted(all_dates_hours, key=lambda dh: (
        datetime.strptime(dh.split()[0], '%Y-%m-%d'),  # Sort by date
        ['7am', '9am', '11am', '1pm', '3pm', '5pm', '7pm', '9pm', '11pm', '1am', '3am', '5am'].index(dh.split()[1])  # Sort by time
    ))

    # Prepare data for Excel output
    export_data = []
    header_row = ["Room"] + sorted_dates_hours  # First row is the header
    export_data.append(header_row)

    # Process all rooms
    all_rooms = sorted(structured_data.keys())
    for room in all_rooms:
        row = [room]
        for date_hour in sorted_dates_hours:
            if date_hour in structured_data[room]:
                # Use a clear and visible separator
                cell = (
                    f"Status: {structured_data[room][date_hour]['turn_status']} - "
                    f"Name1: {structured_data[room][date_hour]['name1']} - "
                    f"Name2: {structured_data[room][date_hour]['name2']}"
                )
            else:
                cell = "No Data"
            row.append(cell)
        export_data.append(row)

    # Convert data into a DataFrame
    df = pd.DataFrame(export_data[1:], columns=export_data[0])  # Exclude header row from the data

    # Write data to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Turn Data')

        # Adjust column widths for better readability
        workbook = writer.book
        worksheet = writer.sheets['Turn Data']
        for i, col in enumerate(df.columns):
            max_width = max(df[col].astype(str).map(len).max(), len(col)) + 5  # Increase width for visibility
            worksheet.set_column(i, i, max_width)

    # Set the pointer of the BytesIO stream to the beginning
    output.seek(0)

    # Create response with Excel file
    response = make_response(output.read())
    response.headers["Content-Disposition"] = "attachment; filename=Turn_Data.xlsx"
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

@app.route('/export_table', methods=['POST'])
def export_table():
    # Get the table data from the request
    table_data = request.json.get('tableData', [])

    # Create a DataFrame from the table data
    if not table_data:
        return jsonify({"error": "No data provided"}), 400

    df = pd.DataFrame(table_data[1:], columns=table_data[0])  # First row is header

    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Turn Data')

    # Set the pointer of the BytesIO stream to the beginning
    output.seek(0)

    # Return the Excel file as a response
    response = make_response(output.read())
    response.headers["Content-Disposition"] = "attachment; filename=Turn_Data.xlsx"
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response


@app.route('/view_turn_data', methods=['GET'])
def view_turn_data():
    unit = request.args.get('unit', '')
    room = request.args.get('room', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Convert start_date and end_date to datetime objects
    try:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        flash("Invalid date format. Please ensure the dates are correct.", "danger")
        return redirect(url_for('view_turn_data'))

    # Fetch data based on filters
    query = TurnTracker.query.filter(
        TurnTracker.datetime >= start_datetime,
        TurnTracker.datetime <= end_datetime
    )
    if unit:
        query = query.filter(TurnTracker.unit == unit)
    if room:
        query = query.filter(TurnTracker.room_number == room)

    # Order by datetime
    query = query.order_by(TurnTracker.datetime.asc())
    entries = query.all()

    # Build turn_data with date and hour fields
    turn_data = []
    for entry in entries:
        turn_data.append({
            "date": entry.datetime.strftime('%Y-%m-%d'),
            "hour": entry.datetime.strftime('%I:%M %p'),
            "unit": entry.unit,
            "room_number": entry.room_number,
            "turn_status": entry.turn_status or "",
            "name1": entry.name1 or "",
            "name2": entry.name2 or ""
        })

    return render_template(
        'view_turn_data.html',
        turn_data=turn_data,
        unit=unit,
        room=room,
        start_date=start_date,
        end_date=end_date
    )

@app.route('/view_turn_data_horizontal', methods=['GET'])
def view_turn_data_horizontal():
    unit = request.args.get('unit', '')
    room = request.args.get('room', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Convert start_date and end_date to datetime objects
    try:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        flash("Invalid date format. Please ensure the dates are correct.", "danger")
        return redirect(url_for('view_turn_data_horizontal'))

    # Fetch data based on filters
    query = TurnTracker.query.filter(
        TurnTracker.datetime >= start_datetime,
        TurnTracker.datetime <= end_datetime
    )
    if unit:
        query = query.filter(TurnTracker.unit == unit)
    if room:
        query = query.filter(TurnTracker.room_number == room)

    # Order by datetime
    query = query.order_by(TurnTracker.datetime.asc())
    entries = query.all()

    # Process data for the horizontal view
    structured_data = {}
    dates_hours = []
    for entry in entries:
        room_number = entry.room_number
        date_hour = entry.datetime.strftime('%Y-%m-%d %I:%M %p')

        if date_hour not in dates_hours:
            dates_hours.append(date_hour)

        if room_number not in structured_data:
            structured_data[room_number] = {}
        structured_data[room_number][date_hour] = {
            'turn_status': entry.turn_status or '',
            'name1': entry.name1 or '',
            'name2': entry.name2 or ''
        }

    # Sort dates and hours chronologically using datetime parsing
    dates_hours.sort(key=lambda dh: datetime.strptime(dh, '%Y-%m-%d %I:%M %p'))

    return render_template(
        'view_turn_data_horizontal.html',
        unit=unit,
        room=room,
        start_date=start_date,
        end_date=end_date,
        dates_hours=dates_hours,
        structured_data=structured_data
    )

@app.template_filter('datetimeformat')
def datetimeformat(value):
    date_obj = datetime.strptime(value, '%Y-%m-%d')
    return date_obj.strftime('%m/%d/%y')

@app.route('/print_turn_page/<unit>', methods=['GET'])
def print_turn_page(unit):
    shift = request.args.get('shift', 'Days')
    date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))

    # Parse and generate time slots
    base_date = datetime.strptime(date, '%Y-%m-%d')
    next_date = base_date + timedelta(days=1)

    if shift.lower() == 'nights':
        hours = [
            base_date.replace(hour=19).strftime('%Y-%m-%d %I:%M %p'),
            base_date.replace(hour=21).strftime('%Y-%m-%d %I:%M %p'),
            base_date.replace(hour=23).strftime('%Y-%m-%d %I:%M %p'),
            next_date.replace(hour=1).strftime('%Y-%m-%d %I:%M %p'),
            next_date.replace(hour=3).strftime('%Y-%m-%d %I:%M %p'),
            next_date.replace(hour=5).strftime('%Y-%m-%d %I:%M %p')
        ]
    else:
        hours = [
            base_date.replace(hour=7).strftime('%Y-%m-%d %I:%M %p'),
            base_date.replace(hour=9).strftime('%Y-%m-%d %I:%M %p'),
            base_date.replace(hour=11).strftime('%Y-%m-%d %I:%M %p'),
            base_date.replace(hour=13).strftime('%Y-%m-%d %I:%M %p'),
            base_date.replace(hour=15).strftime('%Y-%m-%d %I:%M %p'),
            base_date.replace(hour=17).strftime('%Y-%m-%d %I:%M %p')
        ]

    # Load room data
    all_rooms = load_rooms()
    active_rooms = all_rooms.get(unit, [])

    # Initialize room_data
    room_data = {room: {hour: {"turn_status": ""} for hour in hours} for room in active_rooms}

    # Initialize names
    names = {hour: {"name1": "", "name2": ""} for hour in hours}

    # Query database for entries
    entries = TurnTracker.query.filter(
        TurnTracker.unit == unit,
        TurnTracker.datetime >= datetime.strptime(hours[0], '%Y-%m-%d %I:%M %p'),
        TurnTracker.datetime <= datetime.strptime(hours[-1], '%Y-%m-%d %I:%M %p')
    ).all()

    # Populate room_data and names
    for entry in entries:
        room = entry.room_number
        hour_key = entry.datetime.strftime('%Y-%m-%d %I:%M %p')
        if room in room_data and hour_key in room_data[room]:
            room_data[room][hour_key] = {
                "turn_status": entry.turn_status or ""
            }
        if hour_key in names:
            names[hour_key] = {
                "name1": entry.name1 or "",
                "name2": entry.name2 or ""
            }

    return render_template(
        'print_turn_page.html',
        unit=unit,
        shift=shift,
        date=date,
        hours=hours,
        room_data=room_data,
        names=names  # Pass the names dictionary to the template
    )

if __name__ == "__main__":
    with app.app_context():
        # Only run migrations in development or set up a proper schema
        # db.create_all()  # Avoid this in production, use migrations instead
        print(app.url_map)  # Print routes for debugging
    app.run(host='0.0.0.0', port=8080, debug=False)  # Use port 8080 for cloud
