from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Database setup
def init_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="consultation_db"
    )
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(255)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS interactions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        question TEXT,
        response TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        age INT,
        gender VARCHAR(50),
        address TEXT,
        phone VARCHAR(20),
        email VARCHAR(255),
        domicile VARCHAR(255),
        healthcare VARCHAR(255),
        specialist VARCHAR(255),
        schedule DATETIME
    )''')
    conn.commit()
    conn.close()

# Define the rules for diagnosis with empathetic responses
diagnosis_rules = [
    {"question": "Halooo, Perkenalkan aku BublyMind🥰. Salam kenal yaa, kamu boleh ceritakan apa saja kepadaku lohh!! BTW Gimana kabar kamu nihh? 🤗🤗 Sebelumnya aku pengen tau tentang kamuuu, Apakah akhir-akhir ini kamu sedang ngerasa sedih atau kosong? Semoga tidak yaa", 
     "key": "kesedihan", 
     "positive_response": "Merasa sedih itu wajar, tapi kalau terus-menerus, bisa jadi tanda depresi ringan.",
     "response": "Kamu mungkin mengalami gejala awal depresi."},
    {"question": "Seperti itu yaa. Kalo kamu merasa sedih itu wajar banget kokk, tapi kalau terus-menerus, itu ga baik loh.🙁🙁 Oiya, akhit-akhir ini kualitas tidurmu gimanaa? Apakah kamu sulit untuk tidur atau sering terbangun di malam hari?", 
     "key": "tidur", 
     "positive_response": "Gangguan tidur bisa sangat mempengaruhi kesehatan mental.",
     "response": "Masalah tidur bisa menjadi indikasi stres atau kecemasan."},
    {"question": "Oalaa begituuu, semoga kamu tetap mendapat tidur yang cukup yaa... Mmm aku mau tanyaa, Apakah kamu merasa cemas atau khawatir secara berlebihan terhadap banyak hal?", 
     "key": "kecemasan", 
     "positive_response": "Kecemasan yang berlebihan bisa mengganggu aktivitas harian. Penting untuk memahami penyebabnya.",
     "response": "Indikasi kecemasan berlebih ditemukan."},
    {"question": "Kalo begituu, Apakah nafsu makanmu berubah drastis? Atau apakah kamu makan terlalu banyak atau terlalu sedikit?", 
     "key": "nafsu_makan", 
     "positive_response": "Perubahan nafsu makan bisa menjadi tanda adanya masalah kesehatan mental.",
     "response": "Perubahan nafsu makan bisa menjadi gejala depresi atau gangguan makan."},
    {"question": "Mmmm... Jika seperti itu, Apakah kamu sering merasa lelah atau kehilangan energi, meskipun sudah cukup istirahat?", 
     "key": "energi", 
     "positive_response": "Kelelahan yang berkepanjangan bisa menjadi tanda adanya masalah kesehatan fisik atau mental.",
     "response": "Kelelahan kronis bisa menjadi gejala depresi atau gangguan lainnya."},
    {"question": "Baikk, aku mau tanya lagi niihh, Apakah kamu merasa sulit berkonsentrasi atau mengambil keputusan?", 
     "key": "konsentrasi", 
     "positive_response": "Sulit berkonsentrasi bisa mengganggu produktivitas dan kualitas hidup.",
     "response": "Masalah konsentrasi bisa menjadi tanda depresi atau kecemasan."},
    {"question": "Oalaa semoga kamu tetap punya konsentrasi yang baik yaa, mau tanyaa niii, Apakah kamu sering merasa tidak berharga atau bersalah?", 
     "key": "harga_diri", 
     "positive_response": "Perasaan tidak berharga bisa sangat menyiksa. Kamu tidak sendiri.",
     "response": "Perasaan tidak berharga bisa menjadi gejala depresi."},
    {"question": "Terkadang memang beberapa orang merasa seperti itu kok, kamu ga sendiriann. Memang sangat melelahkann... Kalo gitu, Bubly mau tanya Apakah kamu sering merasa ingin menyakiti diri sendiri atau mengakhiri hidup?", 
     "key": "sikap_destruktif", 
     "positive_response": "Jika kamu memiliki pikiran seperti ini, sangat penting untuk mencari bantuan segera.",
     "response": "Pikiran untuk menyakiti diri sendiri adalah kondisi serius yang membutuhkan perhatian medis."},
    {"question": "Semoga kamu selalu dikuatkan yaaa. Apakah kamu merasa terisolasi dari orang-orang yang kamu cintai?", 
     "key": "sosial", 
     "positive_response": "Menarik diri dari orang-orang yang kita sayangi bisa memperburuk kondisi.",
     "response": "Mengisolasi diri bisa menjadi tanda depresi atau gangguan kecemasan sosial."},
    {"question": "Okee, selanjutnya aku mau tanyaa Apakah kamu sering mengalami perubahan suasana hati yang drastis, dari sangat senang menjadi sangat sedih dalam waktu singkat?", 
     "key": "suasana_hati", 
     "positive_response": "Perubahan suasana hati yang ekstrim bisa menjadi tanda gangguan bipolar.",
     "response": "Fluktuasi suasana hati yang cepat bisa menjadi indikasi gangguan bipolar."},
    {"question": "Suasana atau hati emang ga ketebak Bubly terkadang jg begitu kok hehe😆. Baikk, Bubly mau tanyaa, Apakah kamu sering mengalami mimpi buruk atau kilas balik yang mengganggu?", 
     "key": "mimpi_buruk", 
     "positive_response": "Mimpi buruk bisa menjadi tanda stres atau trauma.",
     "response": "Mimpi buruk dan kilas balik bisa menjadi gejala PTSD (Post-Traumatic Stress Disorder)."},
    {"question": "Mimpi emang gabisa ketebak yaaa, kadang baik kadang burukkk. Okedehh, Bubly mau tanya lagiii, Apakah kamu merasa tubuhmu sering sakit-sakitan, meskipun hasil pemeriksaan medis menunjukkan tidak ada masalah fisik yang serius?", 
     "key": "fisik", 
     "positive_response": "Terkadang, masalah kesehatan mental bisa memanifestasikan diri dalam bentuk gejala fisik.",
     "response": "Gejala fisik yang tidak dapat dijelaskan secara medis bisa terkait dengan gangguan kecemasan atau depresi."}
]

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

# List of doctors for appointment dropdown
doctors = [
    {"name": "Dr. Budi Santoso", "specialist": "Psikolog Klinis"},
    {"name": "Dr. Maya Indrawati", "specialist": "Psikiater"},
    {"name": "Dr. Ryan Pratama", "specialist": "Konselor Mental"},
    {"name": "Dr. Siti Rahayu", "specialist": "Terapis Kognitif"},
]

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        domicile = request.form['domicile']
        healthcare = request.form['healthcare']
        specialist = request.form['specialist']
        schedule = request.form['schedule']

        # Save to database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="consultation_db"
        )
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO appointments (name, age, gender, address, phone, email, domicile, healthcare, specialist, schedule) 
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                       (name, age, gender, address, phone, email, domicile, healthcare, specialist, schedule))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('appointment.html', doctors=doctors)

@app.route('/article')
def article():
    return render_template('article.html')

@app.route('/start_chat', methods=['GET'])
def start_chat():
    # Reset session
    session.clear()
    session['answers'] = []
    session['positive_responses'] = []
    session['current_question'] = 0

    # Return first question
    first_question = diagnosis_rules[0]['question']
    return jsonify({
        'question': first_question,
        'is_first': True
    })

@app.route('/process_answer', methods=['POST'])
def process_answer():
    user_input = request.json.get('answer', '').lower()

    # Ensure session variables exist
    if 'answers' not in session:
        session['answers'] = []
    if 'positive_responses' not in session:
        session['positive_responses'] = []
    if 'current_question' not in session:
        session['current_question'] = 0

    current_question = session['current_question']
    answers = session['answers']
    positive_responses = session['positive_responses']

    # Save answer
    answers.append(user_input)

    # Add positive response if the answer is affirmative
    if user_input in ["ya", "iya", "yes", "y"]:
        positive_responses.append(diagnosis_rules[current_question]['positive_response'])
        bot_response = diagnosis_rules[current_question]['positive_response']
    else:
        bot_response = "Terima kasih atas jawabanmu."

    # Move to next question
    current_question += 1
    session['current_question'] = current_question

    # Check if we've reached the end
    if current_question >= len(diagnosis_rules):
        # Generate diagnosis
        diagnosis = []
        for i, rule in enumerate(diagnosis_rules):
            if answers[i] in ["ya", "iya", "iyaa", "iyah", "iyh"]:
                diagnosis.append(rule['response'])

        # Combine positive responses and diagnoses
        result_message = "Berdasarkan percakapan kita:\n\n"

        # Add positive responses first
        if positive_responses:
            result_message += "Hal-hal yang kamu alami:\n"
            result_message += "\n".join(positive_responses)
            result_message += "\n\n"

        # Add diagnoses
        if diagnosis:
            result_message += "Indikasi kesehatan mental:\n"
            result_message += "\n".join(diagnosis)
        else:
            result_message += "\n Kamu tampaknya dalam kondisi kesehatan mental yang baik.\n"

        result_message += "\n\n Ingat, ini hanya asesmen awal. Selalu disarankan untuk berkonsultasi dengan profesional kesehatan mental untuk diagnosis yang komprehensif."

        return jsonify({
            'is_complete': True,
            'result': result_message,
            'appointment_link': '/appointment'
        })

    # Return bot response and next question
    next_question = diagnosis_rules[current_question]['question']
    return jsonify({
        'bot_response': bot_response,
        'question': next_question,
        'is_complete': current_question >= len(diagnosis_rules)
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)