from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
# Database setup
database = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-movies.db"
database.init_app(app)
# Movie request setup
API_KEY = '296a1e408f854fefa4bfdb5371efb96a'
url = 'https://api.themoviedb.org/3/search/movie'
headers = {
    "Authorization": "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyOTZhMWU0MDhmODU0ZmVmYTRiZmRiNTM3MWVmYjk2YSIsInN1YiI6IjY1ODMyMDZjZTI5NWI0M2JjNzY4NzkyNCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.gGSxuao0hM28Qf0b3V8rmuWvY9cflBKVVuMkvu-eJI8",
}
parameters = {
    'api_key': '296a1e408f854fefa4bfdb5371efb96a',
    'query': 'movie_name',
}


class Movie(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    title = database.Column(database.String, unique=True, nullable=False)
    year = database.Column(database.Integer, nullable=False)
    description = database.Column(database.String, nullable=False)
    rating = database.Column(database.Float, nullable=True)
    ranking = database.Column(database.Integer, nullable=True)
    review = database.Column(database.String, nullable=True)
    img_url = database.Column(database.String, nullable=False)

    def __repr__(self):
        return f'<Book {self.title}>'


with app.app_context():
    database.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


class AddNewMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    query = database.select(Movie).order_by(Movie.rating)
    sorted_result = database.session.execute(query)
    all_movies = sorted_result.scalars().all()

    # Assign rank
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    database.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route('/add', methods=['POST', 'GET'])
def add():
    form = AddNewMovie()
    if request.method == 'POST':
        movie_name = form.title.data
        parameters['query'] = movie_name
        movies_response = requests.get(url=url, headers=headers, params=parameters)
        data = movies_response.json()['results']
        return render_template('select.html', options=data)
    return render_template('add.html', form=form)


@app.route('/select', methods=['POST', 'GET'])
def select():
    return render_template('select.html')


@app.route('/edit', methods=['POST', 'GET'])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get('id')
    movie = database.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        database.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form)


@app.route('/delete')
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = database.get_or_404(Movie, movie_id)
    database.session.delete(movie_to_delete)
    database.session.commit()
    return redirect(url_for('home'))


@app.route('/find')
def find_movie():
    movie_api_id = request.args.get('movie_id')
    movie_api_url = f'https://api.themoviedb.org/3/movie/{movie_api_id}'
    response = requests.get(url=movie_api_url, params={'api_key': parameters['api_key'], 'language': 'en-US'})
    data = response.json()
    new_movie = Movie(
        title=data['title'],
        year=data['release_date'].split("-")[0],
        description=data['overview'],
        rating=1.0,
        img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}",
    )
    database.session.add(new_movie)
    database.session.commit()
    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
