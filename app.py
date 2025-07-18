from flask import Flask, request, render_template, jsonify ,redirect, url_for, session
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
from colorama import Fore, Style
import pywhatkit as kit


app = Flask(__name__)

app.secret_key = '11231'

conn = sqlite3.connect('database.db')  


cursor = conn.cursor()


cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        identity_number TEXT UNIQUE,
                        address TEXT,
                        phone_number TEXT,
                        user_type TEXT)''')


cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            blood_pressure REAL NOT NULL,
            diabetes REAL NOT NULL,
            SpO2 REAL NOT NULL,
            BPM REAL NOT NULL
        )
    ''')


conn.commit()


conn.close()

print("تم إنشاء قاعدة البيانات والجداول بنجاح.")


def process_blood_pressure(bp_string):
    try:

        if '/' in str(bp_string):

            systolic, diastolic = str(bp_string).split('/')
            return float(systolic) 
        else:
            return float(bp_string)
    except ValueError:
        return None 

  

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/view')
def view():
   # return render_template('view.html')
    user_role = session.get('user_role', 'مستخدم غير معروف')
    user_idno = session.get('user_idno', 'مستخدم غير معروف')
    return render_template('view.html', user_role=user_role,user_idno=user_idno)


@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/index2')
def index2():
    return render_template('index2.html')

@app.route('/index3')
def index3():
    user_role = session.get('user_role', 'مستخدم غير معروف')
    user_idno = session.get('user_idno', 'مستخدم غير معروف')
    return render_template('index3.html', user_role=user_role,user_idno=user_idno)

   # return render_template('index3.html')


@app.route('/Menu')
def Menu():
    user_role = session.get('user_role', 'مستخدم غير معروف')
    user_idno = session.get('user_idno', 'مستخدم غير معروف')
    return render_template('Menu.html', user_role=user_role,user_idno=user_idno)

@app.route('/upload')
def Upload():
    return render_template('Upload.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
       
        if 'file' not in request.files:
            return jsonify({"error": "ملف غير موجود في الطلب"}), 400
        
        file = request.files['file']
        
       
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "يرجى رفع ملف CSV فقط"}), 400
        
       
        df = pd.read_csv(file)
        
       
        expected_columns = ['timestamp', 'temperature', 'blood_pressure', 'diabetes']
        if not all(col in df.columns for col in expected_columns):
            return jsonify({"error": f"الملف يجب أن يحتوي على الأعمدة التالية: {', '.join(expected_columns)}"}), 400 
        
       
        df['blood_pressure'] = df['blood_pressure'].apply(process_blood_pressure)

       
        text_analysis = f"تم تحليل {len(df)} سجلات.\n"
        text_analysis += f"المتوسط العام لدرجة الحرارة هو {df['temperature'].mean():.2f}°C.\n"

       
        avg_diabetes = df['diabetes'].mean()
        if avg_diabetes > 6.0:
            text_analysis += f"معدل السكري مرتفع بمتوسط {avg_diabetes:.2f}. يوصى بمراجعة الطبيب.\n"
        else:
            text_analysis += f"معدل السكري طبيعي بمتوسط {avg_diabetes:.2f}.\n"

       
        avg_blood_pressure = df['blood_pressure'].mean()
        if avg_blood_pressure > 120:
            text_analysis += f"ضغط الدم مرتفع بمتوسط {avg_blood_pressure:.2f}. يوصى بمراجعة الطبيب.\n"
        else:
            text_analysis += f"ضغط الدم طبيعي بمتوسط {avg_blood_pressure:.2f}.\n"
        
      
       
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(data=df, x='timestamp', y='temperature', label='temperature', ax=ax)
        sns.lineplot(data=df, x='timestamp', y='blood_pressure', label='blood_pressure', ax=ax)
        sns.lineplot(data=df, x='timestamp', y='diabetes', label='diabetes', ax=ax)
        ax.set_title('Date Patients')
        ax.set_xlabel('Date/time')
        ax.set_ylabel('Mesures')
        
       
        img_stream = io.BytesIO()
        plt.savefig(img_stream, format='png')
        img_stream.seek(0)
        img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')

        return jsonify({
            'textAnalysis': text_analysis,
            'imageBase64': img_base64
        })


    except Exception as e:
        return jsonify({"error": str(e)}), 500

   
def check_identity(identity_number):
         conn = sqlite3.connect('database.db')
         cursor = conn.cursor()
         cursor.execute('''SELECT * FROM users WHERE identity_number = ?''', (identity_number,))
         result = cursor.fetchone()
         conn.close()
         return result

   
@app.route('/login_user', methods=['POST'])
def login_user():
    identity_number = request.form['identity_number']
    user = check_identity(identity_number)

    if user:
   
        session['user_role'] = user[1]
        session['user_idno'] = user[2]
        session['user_mobile'] = user[4]
        return redirect(url_for('Menu'))
    else:
        return 'رقم الهوية غير موجود. الرجاء التسجيل أولاً.'

def add_user(name, identity_number, address, phone_number, user_type):
    try:
         conn = sqlite3.connect('database.db')
         cursor = conn.cursor()
         cursor.execute('''INSERT  INTO users (name, identity_number, address, phone_number, user_type)
                      VALUES (?, ?, ?, ?, ?)''', (name, identity_number, address, phone_number, user_type))
         conn.commit()

         print("تم إضافة البيانات بنجاح!")

    except sqlite3.IntegrityError as e:
        print(f"خطأ: {e}. رقم الهوية موجود بالفعل!")
    finally:
         conn.close()



   
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        identity_number = request.form['identity_number']
        address = request.form['address']
        phone_number = request.form['phone_number']
        user_type = request.form['user_type']  # مريض أو دكتور

       
        add_user(name, identity_number, address, phone_number, user_type)
        #return redirect(url_for('index'))
        session['user_role'] = name
        return redirect(url_for('Menu'))
    
    return render_template('register.html')



@app.route('/analyze2', methods=['POST'])
def analyze2():
    try:
       
        if 'file' not in request.files:
            return jsonify({"error": "ملف غير موجود في الطلب"}), 400
        
        file = request.files['file']
        
       
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "يرجى رفع ملف CSV فقط"}), 400
        
       
        df = pd.read_csv(file)
        
       
        expected_columns = ['timestamp', 'temperature', 'blood_pressure', 'diabetes']
        if not all(col in df.columns for col in expected_columns):
            return jsonify({"error": f"الملف يجب أن يحتوي على الأعمدة التالية: {', '.join(expected_columns)}"}), 400 
        
       
        df['blood_pressure'] = df['blood_pressure'].apply(process_blood_pressure)

       
        text_analysis = f"تم تحليل {len(df)} سجلات.\n"
        text_analysis += f"المتوسط العام لدرجة الحرارة هو {df['temperature'].mean():.2f}°C.\n"

       
        avg_diabetes = df['diabetes'].mean()
        diabetes_alert = False
        if avg_diabetes > 6.0:
            text_analysis += f"معدل السكري مرتفع بمتوسط {avg_diabetes:.2f}. يوصى بمراجعة تتت الطبيب.\n"
            diabetes_alert = True
        else:
            text_analysis += f"معدل السكري طبيعي تتت بمتوسط {avg_diabetes:.2f}.\n"

       
        avg_blood_pressure = df['blood_pressure'].mean()
        blood_pressure_alert = False
        if avg_blood_pressure > 120:
            text_analysis += f"ضغط الدم مرتفع بمتوسط {avg_blood_pressure:.2f}. يوصى بمراجعة تتت الطبيب.\n"
            blood_pressure_alert = True
        else:
            text_analysis += f"ضغط الدم طبيعي تتت بمتوسط {avg_blood_pressure:.2f}.\n"

       
        avg_temperature = df['temperature'].mean()
        temperature_alert = False
        if avg_temperature > 37.5: 
            text_analysis += f"درجة الحرارة مرتفعة بمتوسط {avg_temperature:.2f}°C. يوصى بمراجعة  الطبيب.\n"
            temperature_alert = True
        else:
            text_analysis += f"درجة الحرارة طبيعية تتت بمتوسط {avg_temperature:.2f}°C.\n"
        
       
        if diabetes_alert or blood_pressure_alert or temperature_alert:
            send_email_alert(diabetes_alert, blood_pressure_alert, temperature_alert)

       
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(data=df, x='timestamp', y='temperature', label='temperature', ax=ax)
        sns.lineplot(data=df, x='timestamp', y='blood_pressure', label='blood_pressure', ax=ax)
        sns.lineplot(data=df, x='timestamp', y='diabetes', label='diabetes', ax=ax)
        ax.set_title('Date Patients')
        ax.set_xlabel('Date/time')
        ax.set_ylabel('Mesures')
        
      
        img_stream = io.BytesIO()
        plt.savefig(img_stream, format='png')
        img_stream.seek(0)
        img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')

        return jsonify({
            'textAnalysis': text_analysis,
            'imageBase64': img_base64
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/analyze3', methods=['POST'])
def analyze3():
    try:
      
        if 'file' not in request.files:
            return jsonify({"error": "ملف غير موجود في الطلب"}), 400
        
        file = request.files['file']
        
      
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "يرجى رفع ملف CSV فقط"}), 400
        
        
        df = pd.read_csv(file)
        
        
        expected_columns = ['timestamp', 'temperature', 'blood_pressure', 'diabetes', 'SpO2', 'BPM']
        if not all(col in df.columns for col in expected_columns):
            return jsonify({"error": f"الملف يجب أن يحتوي على الأعمدة التالية: {', '.join(expected_columns)}"}), 400 
        
        
        df['blood_pressure'] = df['blood_pressure'].apply(process_blood_pressure)
        
        text_analysis = f" There are {len(df)}"
        text_analysis += f" records that were analyzed\n"
       

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO health_records (
                    patient_id, timestamp, temperature, blood_pressure, diabetes, SpO2, BPM
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['user_idno'], row['timestamp'], row['temperature'],
                row['blood_pressure'], row['diabetes'], row['SpO2'], row['BPM']
            ))
        conn.commit()
        conn.close()        

       
        avg_diabetes = df['diabetes'].mean()
        diabetes_alert = False
        if avg_diabetes > 6.0:
            text_analysis += f"The diabetes rate is high on average {avg_diabetes:.2f}. It is advised to see a doctor\n"
            diabetes_alert = True
        else:
            text_analysis += f"The diabetes rate is normal on average {avg_diabetes:.2f}\n"

       
        avg_blood_pressure = df['blood_pressure'].mean()
        blood_pressure_alert = False
        if avg_blood_pressure > 120:
            text_analysis += f"The blood pressure rate is high on average {avg_blood_pressure:.2f}. It is advised to see a doctor\n"            
            blood_pressure_alert = True
        else:
            text_analysis += f"The blood pressure is normal on average {avg_blood_pressure:.2f}\n"

       
        avg_temperature = df['temperature'].mean()
        temperature_alert = False
        if avg_temperature > 37.5: 
            text_analysis += f"The temperature rate is high on average {avg_temperature:.2f}°C. It is advised to see a doctor\n"
            temperature_alert = True
        else:
            text_analysis += f"The temperature rate is normal on average {avg_temperature:.2f}°C\n"
        
      
        avg_spo2 = df['SpO2'].mean()
        spo2_alert = False
        if avg_spo2 < 90:
            text_analysis += f"The SpO2 rate is low on average {avg_spo2:.2f}%. It is advised to see a doctor\n"
            spo2_alert = True
        else:
            text_analysis += f"The SpO2 rate is normal on average {avg_spo2:.2f}%\n"

      
        avg_bpm = df['BPM'].mean()
        bpm_alert = False
        if avg_bpm < 60 or avg_bpm > 100:
            text_analysis += f"The heartbeat is abnormal on average {avg_bpm:.2f} BPM. It is advised to see a doctor\n"            

            bpm_alert = True
        else:
            text_analysis += f"The heartbeat is normal on average {avg_bpm:.2f} BPM\n"

       
        if diabetes_alert or blood_pressure_alert or temperature_alert or spo2_alert or bpm_alert:
            send_email_alert2(diabetes_alert, blood_pressure_alert, temperature_alert, spo2_alert, bpm_alert)

        if diabetes_alert or blood_pressure_alert or temperature_alert or spo2_alert or bpm_alert:
           phone_number = session['user_mobile']
           message = "Urgent Message: It is advised to see a doctor " + session['user_role'] 
           kit.sendwhatmsg_instantly(phone_number, message)


       
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(data=df, x='timestamp', y='temperature', label='Temperature', ax=ax)
        sns.lineplot(data=df, x='timestamp', y='blood_pressure', label='Blood Pressure', ax=ax)
        sns.lineplot(data=df, x='timestamp', y='diabetes', label='Diabetes', ax=ax)
        sns.lineplot(data=df, x='timestamp', y='SpO2', label='SpO2', ax=ax)
        sns.lineplot(data=df, x='timestamp', y='BPM', label='BPM', ax=ax)
        ax.set_title('Health Parameters Analysis')
        ax.set_xlabel('Timestamp')
        ax.set_ylabel('Values')
        
       
        img_stream = io.BytesIO()
        plt.savefig(img_stream, format='png')
        img_stream.seek(0)
        img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')

        return jsonify({
            'textAnalysis': text_analysis,
            'imageBase64': img_base64
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


  
def send_email_alert(diabetes_alert, blood_pressure_alert, temperature_alert):
   
       
        sender_email = "raminafee11@gmail.com"
        receiver_email = "raminafee11@example.com"
        password = "ksvz cgft eglg uvtm"
        
      
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = "تنبيه: مشكلة صحية محتملة"
        
        body = "تم اكتشاف حالة صحية غير طبيعية في البيانات التي تم تحليلها.\n"
        if diabetes_alert:
            body += "معدل السكري مرتفع.\n"
        if blood_pressure_alert:
            body += "ضغط الدم مرتفع.\n"
        if temperature_alert:
            body += "درجة الحرارة مرتفعة.\n"
        
        msg.attach(MIMEText(body, 'plain'))

      
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())

def send_email_alert2(diabetes_alert, blood_pressure_alert, temperature_alert, spo2_alert, bpm_alert):
   
      
        sender_email = "raminafee11@gmail.com"
        receiver_email = "raminafee11@example.com"
        password = "ksvz cgft eglg uvtm"
        
      
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = "تنبيه: مشكلة صحية محتملة"
        
        body = "تم اكتشاف حالة صحية غير طبيعية في البيانات التي تم تحليلها.\n"
        if diabetes_alert:
            body += "معدل السكري مرتفع.\n"
        if blood_pressure_alert:
            body += "ضغط الدم مرتفع.\n"
        if temperature_alert:
            body += "درجة الحرارة مرتفعة.\n"
        if spo2_alert:
            body += "درجة الاكسجين مرتفعة.\n"
        if bpm_alert:
            body += " نبضات القلب مرتفعة.\n"
        
        msg.attach(MIMEText(body, 'plain'))

      
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
    

@app.route('/get_records', methods=['GET'])
def get_records():
    try:
      
        patient_id = session['user_idno']
        if not patient_id:
            return jsonify({"error": "رقم الهوية مفقود"}), 400
        
      
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
      
        cursor.execute('''
            SELECT timestamp, temperature, blood_pressure, diabetes, SpO2, BPM
            FROM health_records
            WHERE patient_id = ?
            ORDER BY timestamp DESC
        ''', (patient_id,))
        
      
        rows = cursor.fetchall()
        conn.close()
        
      
        records = [
            {
                "timestamp": row[0],
                "temperature": row[1],
                "blood_pressure": row[2],
                "diabetes": row[3],
                "SpO2": row[4],
                "BPM": row[5]
            }
            for row in rows
        ]
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/upload', methods=['POST'])
def upload():
     if 'filex' not in request.files:
        return jsonify({"error": "ملف غير موجود في الطلب"}), 400

     file = request.files['filex']
 
     if file.filename == '':
        flash('لم يتم اختيار أي ملف')
        return redirect(request.url)
    
    
     if file and file.filename.endswith('.csv'):
        try:
    
            df = pd.read_csv(file)

    
            expected_columns = ['timestamp', 'temperature', 'blood_pressure', 'diabetes']
            
    
            if all(col in df.columns for col in expected_columns):
    
                data = df.head(5).to_dict(orient='records')
                return render_template('Upload.html', data=data)
            else:
                flash(f'الأعمدة غير صحيحة. يجب أن تحتوي على الأعمدة: {", ".join(expected_columns)}')
                return redirect('/upload')
        except Exception as e:
            flash(f'حدث خطأ أثناء قراءة الملف: {str(e)}')
            return redirect('/upload')
     else:
        flash('يرجى تحميل ملف CSV فقط')
        return redirect('/upload')

if __name__ == "__main__":
    app.run(debug=True)



