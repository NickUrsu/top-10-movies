from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:////my-favorite-movies.db")
Bootstrap(app)
db = SQLAlchemy(app)
api_key = os.environ.get("API_KEY")

class EditForm(FlaskForm):
    rating = StringField('Your rating out of 10, eg.:7.4', validators=[DataRequired()])
    review = TextAreaField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')

class AddByTitleForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(255))
    img_url = db.Column(db.String(255), nullable=False)


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    db.session.commit()
    movies = Movie.query.order_by(Movie.ranking).all()

    return render_template("index.html", movies=movies)


@app.route('/edit/<item_id>', methods=['GET', 'POST'])
def edit(item_id):
    movie = Movie.query.get(item_id)
    edit_form = EditForm()
    if edit_form.validate_on_submit():
        movie.rating = edit_form.rating.data
        movie.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template('edit.html', movie=movie, edit_form=EditForm())


@app.route('/delete/<item_id>')
def delete(item_id):
    movie_to_delete = Movie.query.get(item_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['POST', 'GET'])
def add_movie():
    add_form = AddByTitleForm()
    if add_form.validate_on_submit():
        api_params = {'api_key': api_key, 'query': add_form.title.data, 'page': 1}
        result = requests.get(url="https://api.themoviedb.org/3/search/movie", params=api_params).json()
        all_movies = result['results']
        return render_template('select.html', movies=all_movies)
    return render_template('add.html', add_form=add_form)


@app.route('/select/<movie_id>')
def select(movie_id):
    api_params = {'api_key': api_key}
    result = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_id}", params=api_params).json()
    new_movie = Movie(title=result['original_title'],
                      year=result['release_date'][:4],
                      description=result['overview'],
                      img_url=f"https://image.tmdb.org/t/p/original/{result['poster_path']}",
                      rating=0)
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', item_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
