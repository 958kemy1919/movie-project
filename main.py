from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests

API_KEY = "15d597bc57f87b9c676f1de5e40a0197"
URL_ENDPOINT = "https://api.themoviedb.org/3/search/movie"


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(app)
Bootstrap(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String,unique=True,nullable=False)
    year = db.Column(db.Integer,nullable=False)
    description = db.Column(db.String,nullable=False)
    rating = db.Column(db.Float,nullable=True)
    ranking = db.Column(db.Integer,nullable=True)
    review = db.Column(db.String,nullable=True)
    img_url = db.Column(db.String,nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating)
    db.session.commit()
    return render_template("index.html",movies=movies)

class MyFormEdit(FlaskForm):
    rating = FloatField('Your rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review',validators=[DataRequired()])
    submit = SubmitField('Done')


@app.route('/edit', methods = ["POST", "GET"])
def edit():
    form = MyFormEdit()
    movie_id = request.args.get('id')
    movie_title = request.args.get('title')
    print(movie_id)
    if form.validate_on_submit():
        rating = form.rating.data
        review = form.review.data
        URL = f"https://api.themoviedb.org/3/movie/{movie_id}"
        parameters = {
            "api_key": API_KEY
        }
        response = requests.get(url=URL, params=parameters)
        movie_data = response.json()

        movies = Movie.query.all()
        ratings = [movie.rating for movie in movies]
        ratings.append(rating)

        def f(x, list):
            num_of_larger = 0
            for l in list:
                if l > x:
                    num_of_larger += 1
            return num_of_larger

        def rank(ratings):
            rankings = []
            for rate in ratings:
                rankings.append(f(rate, ratings) + 1)
            return rankings

        rankings = rank(ratings)
        i = 0
        for movie in movies:
            movie.ranking = rankings[i]
            db.session.commit()
            i += 1

        movie = Movie(title=movie_data['title'], year=movie_data['release_date'].split("-")[0],
                      description=movie_data['overview'],rating=rating,review=review,ranking=rankings[len(movies)],
                      img_url=f"https://image.tmdb.org/t/p/original/{movie_data['poster_path']}")
        db.session.add(movie)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html",form=form,movie_title=movie_title)

@app.route('/delete', methods = ["POST", "GET"])
def delete():
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    movies = Movie.query.all()
    ratings = [movie.rating for movie in movies]
    def f(x, list):
        num_of_larger = 0
        for l in list:
            if l > x:
                num_of_larger += 1
        return num_of_larger

    def rank(ratings):
        rankings = []
        for rate in ratings:
            rankings.append(f(rate, ratings) + 1)
        return rankings

    rankings = rank(ratings)
    i = 0
    for movie in movies:
        movie.ranking = rankings[i]
        db.session.commit()
        i += 1
    return redirect(url_for('home'))

class MyFormAdd(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

@app.route('/add', methods = ["POST", "GET"])
def add():
    form = MyFormAdd()
    if form.validate_on_submit():
        movie_title = form.title.data
        parameters = {
            "query": movie_title,
            "api_key": API_KEY
        }
        response = requests.get(url=URL_ENDPOINT, params=parameters)
        movies = response.json()["results"]
        return render_template("select.html",movies=movies)

    return render_template("add.html",form=form)


if __name__ == '__main__':
    app.run(debug=True)