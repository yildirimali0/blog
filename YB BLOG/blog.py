from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from functools import wraps
from flask_change_password import ChangePassword

#Kullanıcı Giriş Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfayı Görüntülemek İçin Lütfen Giriş Yapın","danger")
            return redirect(url_for("login"))
    return decorated_function

#Kullanıcı kayıt Formu
class Registerform(Form):
    name = StringField("İsim Soyisim",validators=[validators.length(min=4,max=25,message="En az 4 karakterli olmalıdır")])
    username = StringField("Kullanıcı Adı",validators=[validators.length(min=5,max=30)])
    email = StringField("Email Adresi",validators=[validators.Email(message="Lütfen Geçerli Email Adresi Girin")]) #Email Fonksiyonu gerçekten email adresimi diye kontrol eder
    password = PasswordField("Parola",validators=[
        validators.DataRequired(message="Lütfen Bir Parola Belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor")
    ])
    confirm = PasswordField("Parola Doğrula")

class Loginform(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola")

class PasswordForm(Form):
    new_password=PasswordField("Parola",validators=[
        validators.DataRequired(message="Lütfen Bir Parola Belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor")
    ])
    confirm = PasswordField("Parola Doğrula")



app=Flask(__name__)
app.secret_key="ybblog" #Flash message için gerekli
app.config["MYSQL_HOST"] ="localhost" #Eğer sql tabanızım uzakta olsaydu o sunucunun adresini vermemız lazım ama bizim bilgisayarda pldugu ıcın local host yazdık
app.config["MYSQL_USER"] ="root"   #Kullanıcı adı root parola boş olarak geliyor
app.config["MYSQL_PASSWORD"] =""
app.config["MYSQL_DB"]="ybblog" #configin içine ne yazılması gerektiği mysql flask sitesinde detaylı acıkalması var
app.config["MYSQL_CURSORCLASS"]="DictCursor" #Buda fromlarımızı tanıtırıyor

mysql=MySQL(app) #Flask ile mysql'i ilişkisi tamamlandı

@app.route("/homepage")
def homepage():
    return render_template("homepage.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/")
def index():
    return render_template("index.html")



@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    query="Select * From articles where auther = %s"
    result=cursor.execute(query,(session["username"],))
    
    if result>0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)

    else:
        return render_template("dashboard.html")

#Kayıt olma

@app.route("/register",methods = ["GET","POST"])
def register():
    form=Registerform(request.form)

    if request.method=="POST" and form.validate(): #form.valideate eğer formda bir sıkıntı yoksa bu koşula gir demektir
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)
        cursor=mysql.connection.cursor()
        query="Insert into users (name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(query,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla Kayıt Oldunuz","success")
        return redirect(url_for("login")) 

    else:
        return render_template("register.html",form = form)

#Login işlemi
@app.route("/login",methods = ["GET","POST"])
def login():
    form = Loginform(request.form)
    if request.method=="POST":
        username=form.username.data
        password_entered=form.password.data

        cursor=mysql.connection.cursor()

        query="Select * From users where username = %s"
        result=cursor.execute(query,(username,))
        if result>0:
            data = cursor.fetchone()  #Kullanıcının bütün bilgilerinialır
            reel_password = data["password"] #Fetchone komutu sözlük ile dataları getiriyor app.config["MYSQL_CURSORCLASS"]="DictCursor" bu komuttan dolayı,
            if sha256_crypt.verify(password_entered,reel_password): #Parolar yıldızlı olduğu için verify onların normal halini karşılaştırıyor
                flash("Başarıyla Giriş Yaptınız","success")
                session["logged_in"] = True
                session["username"]=username
                return redirect(url_for("homepage"))
            else:
                flash("Yanlış parola girdiniz","danger")
                return redirect(url_for("login"))
                
        else:
            flash("Böyle Bir Kullanıcı Bulunmuyor","danger")
            return redirect(url_for("login"))
    return render_template("login.html",form=form)

#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()
    query="Select * From articles where id=%s"
    result=cursor.execute(query,(id,))
    
    if result>0:
        article=cursor.fetchone()
        return render_template("article.html", article = article)
    else:
        return render_template("article.html")

#Logout İşlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Makale Sayfası
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    query="Select * From articles"
    result=cursor.execute(query)

    if result>0:
        articles=cursor.fetchall()

        return render_template("articles.html",articles=articles)
    
    else:
        return render_template("articles.html")

#Makale Ekleme
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data

        cursor=mysql.connection.cursor()

        query="Insert into articles(title,auther,content) VALUES(%s,%s,%s)"
        cursor.execute(query,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        
        flash("Makeleniz Başarıyla Eklendi","success")
        
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form = form)

#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    query="Select * From articles where auther=%s and id=%s"
    result=cursor.execute(query,(session["username"],id))
    if result>0:
        query2="Delete from articles where id=%s"
        cursor.execute(query2,(id,))
        mysql.connection.commit()
        flash("Makaleniz silindi","danger")
        return redirect(url_for("dashboard"))
    
    

    else:
        flash("Bu makale size ait değil ya da böyle bir makale yok","danger")
        return redirect(url_for("index"))


#Makale Güncelle
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        query="Select * From articles where id=%s and auther=%s"
        result=cursor.execute(query,(id,session["username"]))
        if result==0:
            flash("Bu makale size ait değil ya da böyle bir makale yok","danger")
            return redirect(url_for("index"))
        
        else:
            article=cursor.fetchone()
            form=ArticleForm()
            form.title.data = article["title"]
            form.content.data= article["content"]

            return render_template("update.html",form=form)
    else:
        #Post reques kısmı
        form=ArticleForm(request.form)
        newTitle=form.title.data
        newcontent=form.content.data

        query2="Update articles Set title=%s , content=%s where id=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(query2,(newTitle,newcontent,id))
        mysql.connection.commit()
        flash("Makale başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))



#Makale Form
class ArticleForm(Form):
    title= StringField("Makale Başlığı",validators=[validators.length(min=5,max=100)])
    content= TextAreaField("Makale İçeriği",validators=[validators.length(min=10)])

#Arama URL
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword") #html sayfasındakı keyword
        cursor=mysql.connection.cursor()
        query="Select * from articles where title like '%" + keyword + "%' " #keyword ile ilgili şeyleri getiriyor
        result=cursor.execute(query)

        if result==0:
            flash("Aranan kelimeyle ilgili makale bulunamadı","warning")
            return redirect(url_for("articles"))

        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)





#Şifre Değiştirme
@app.route("/password_change/<string:id>", methods=["GET","POST"])
@login_required
def password_change(id):
    form = PasswordForm(request.form)
    if request.method=="POST" and form.validate():
        new_password=sha256_crypt.encrypt(form.new_passwordi.data)
        query="Update users Set password=%s where id=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(query,(new_password,id))
        mysql.connection.commit()
        flash("Parolanız Başarıyla Güncellenmiştir","success")
        return redirect(url_for("login"))
    else:
        return render_template("password_change.html",form=form)



    



        



if __name__=="__main__":
    app.run(debug=True)
