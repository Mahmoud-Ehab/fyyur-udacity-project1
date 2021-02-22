#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
    __tablename__ = 'Show'

    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
    start_date = db.Column(db.DateTime(), nullable=False)


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=True)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(255))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(255))
    genres = db.Column(db.String(120), nullable=False)

    shows = db.relationship('Show', backref='venue', cascade="all, delete-orphan")


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=True)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(255))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(255))

    shows = db.relationship('Show', backref='artist', cascade="all, delete-orphan")


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []

  states_cities = Venue.query.with_entities(Venue.state, Venue.city).group_by(Venue.state, Venue.city).all()

  for sc in states_cities:
      # Initialize the data object
      dataObject = {}

      # Fill in the data object
      dataObject['state'] = sc.state
      dataObject['city'] = sc.city

      venues = []
      localVenues = Venue.query.with_entities(Venue.id, Venue.name).filter(Venue.state==sc.state, Venue.city==sc.city).all()
      for lv in localVenues:
          venueObject = {}
          venueObject['id'] = lv.id
          venueObject['name'] = lv.name
          venues.append(venueObject)

      dataObject['venues'] = venues

      # Append it to the data list
      data.append(dataObject)

  return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  venues = Venue.query.filter(Venue.name.ilike(f"%{request.form['search_term']}%")).all()
  response={
    "count": len(venues),
    "data": []
  }
  for v in venues:
      obj = {
        'id': v.id,
        'name': v.name,
      }
      response['data'].append(obj)

  return render_template('pages/search_venues.html', results=response, search_term=request.form['search_term'])


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    data = {}
    venue = Venue.query.get(venue_id)
    if venue == None:
        return redirect(url_for('index'))

    # Insert atrributes into data
    attributes = ['id', 'name', 'genres', 'address', 'city', 'state', 'phone',
                    'website', 'facebook_link', 'seeking_talent', 'image_link']

    for attr in attributes:
        if attr == 'genres':
            data[attr] = list(getattr(venue, attr)[1:-1].split(","))
            continue
        data[attr] = getattr(venue, attr)

    # Insert upcoming_shows & past_shows
    data['upcoming_shows'] = []
    data['past_shows'] = []
    data['upcoming_shows_count'] = 0
    data['past_shows_count'] = 0

    for s in venue.shows:
        # Initialize the show object
        obj = {
            'artist_id': s.artist.id,
            'artist_name': s.artist.name,
            'artist_image_link': s.artist.image_link,
            'start_time': str(s.start_date),
        }

        # Determine in which list should the object be appended
        timespan = (s.start_date - datetime.now()).total_seconds()
        if (timespan > 0):
            data['upcoming_shows'].append(obj)
            data['upcoming_shows_count'] += 1
        else:
            data['past_shows'].append(obj)
            data['past_shows_count'] += 1

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  successed = True
  try:
      keys = ['name', 'state', 'city', 'address', 'genres', 'phone', 'facebook_link']
      NewVenue = Venue()
      for key in keys:
          if key == 'genres':
              setattr(NewVenue, key, request.form.getlist('genres'))
              continue
          setattr(NewVenue, key, request.form[key])
      db.session.add(NewVenue)
  except:
      successed = False
      db.session.rollback()
  finally:
      db.session.commit()

  # on successful db insert, flash success
  if successed:
      flash(f'Venue {request.form["name"]} was successfully listed!')
  else:
      # TODO: on unsuccessful db insert, flash an error instead.
      flash(f'An error occurred. Venue {request.form["name"]} could not be listed.')

  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  successed = True
  venue = Venue.query.get(venue_id)
  v_name = venue.name
  try:
      db.session.delete(venue)
      db.session.commit()

  except Exception as e:
      successed = False
      print('Error:', e)
      db.session.rollback()

  finally:
      db.session.close()

  # on successful, flash success
  if successed:
      flash(f'Venue {v_name} has been deleted.')
  else:
      # TODO: on unsuccessful, flash an error instead.
      flash(f'An error occurred. Venue {v_name} could not be deleted.')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data=[]

  artists = Artist.query.with_entities(Artist.id, Artist.name).all()
  for artist in artists:
      obj = {
        'id': artist.id,
        'name': artist.name,
      }
      data.append(obj)

  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  artists = Artist.query.filter(Artist.name.ilike(f"%{request.form['search_term']}%")).all()

  response={
    "count": len(artists),
    "data": []
  }

  for a in artists:
      obj = {
        'id': a.id,
        'name': a.name
      }
      response['data'].append(obj)

  return render_template('pages/search_artists.html', results=response, search_term=request.form['search_term'])


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    data = {}
    artist = Artist.query.get(artist_id)
    if artist == None:
        return redirect(url_for('index'))

    # Insert attributes into data object
    attributes = ['id', 'name', 'genres', 'city', 'state', 'phone',
                'website', 'facebook_link', 'seeking_venue', 'image_link']
    for attr in attributes:
      if attr == 'genres':
          data[attr] = list(getattr(artist, attr)[1:-1].split(","))
          continue
      data[attr] = getattr(artist, attr)

    # Insert upcoming_shows & past_shows
    data['upcoming_shows'] = []
    data['past_shows'] = []
    data['upcoming_shows_count'] = 0
    data['past_shows_count'] = 0

    for s in artist.shows:
        # Initialize the show object
        obj = {
            'venue_id': s.venue.id,
            'venue_name': s.venue.name,
            'venue_image_link': s.venue.image_link,
            'start_time': str(s.start_date)
        }

        # Determine in which list should the object be appended
        timespan = (s.start_date - datetime.now()).total_seconds()
        if (timespan > 0):
          data['upcoming_shows'].append(obj)
          data['upcoming_shows_count'] += 1
        else:
          data['past_shows'].append(obj)
          data['past_shows_count'] += 1

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  target = Artist.query.get(artist_id)
  if target == None:
    return redirect(url_for('index'))

  artist={
    "id": target.id,
    "name": target.name,
    "genres": [genre for genre in target.genres[1:-1].split(',')],
    "city": target.city,
    "state": target.state,
    "phone": target.phone,
    "website": target.website,
    "facebook_link": target.facebook_link,
    "seeking_venue": target.seeking_venue,
    "seeking_description": target.seeking_description,
    "image_link": target.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  # Update the artist values
  error = False
  try:
    artist = Artist.query.get(artist_id)

    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']

    db.session.commit()

  except:
    error = True
    db.session.rollback()

  finally:
    db.session.close()

  # Check something wrong happened
  if error:
      flash("Failed. Couldn't update the artist information.")
      return redirect(url_for('index'))
  else:
      flash("Successed.")
      return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  target = Venue.query.get(venue_id)
  if target == None:
    return redirect(url_for('index'))

  venue={
    "id": target.id,
    "name": target.name,
    "genres": [genre for genre in target.genres[1:-1].split(',')],
    'address': target.address,
    "city": target.city,
    "state": target.state,
    "phone": target.phone,
    "website": target.website,
    "facebook_link": target.facebook_link,
    "seeking_talent": target.seeking_talent,
    "seeking_description": target.seeking_description,
    "image_link": target.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

    # Update the venue values
    error = False
    try:
      venue = Venue.query.get(venue_id)

      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.genres = request.form.getlist('genres')
      venue.facebook_link = request.form['facebook_link']

      db.session.commit()

    except:
      error = True
      db.session.rollback()

    finally:
      db.session.close()

    # Check something wrong happened
    if error:
        flash("Failed. Couldn't update the venue information.")
        return redirect(url_for('index'))
    else:
        flash("Successed.")
        return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  successed = True
  try:
      keys = ['name', 'state', 'city', 'genres', 'phone', 'facebook_link']
      NewArtist = Artist()

      for key in keys:
          if key == 'genres':
              setattr(NewArtist, key, request.form.getlist('genres'))
              continue
          setattr(NewArtist, key, request.form[key])

      db.session.add(NewArtist)

  except:
      successed = False
      db.session.rollback()

  finally:
      db.session.commit()

  # on successful db insert, flash success
  if successed:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  # num_shows should be aggregated based on number of upcoming shows per venue.
  data=[]

  shows = Show.query.all()
  for s in shows:
      obj = {
        'venue_id': s.venue_id,
        'venue_name': s.venue.name,
        'artist_id': s.artist_id,
        'artist_name': s.artist.name,
        'artist_image_link': s.artist.image_link,
        'start_time': str(s.start_date)
      }
      data.append(obj)

  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  successed = True
  try:
      v_id = int(request.form['venue_id'])
      a_id = int(request.form['artist_id'])
      date = request.form['start_time']

      # Check if the venue_id exists
      if Venue.query.get(v_id) is None:
          flash('An error occurred. There is no venue with this id.')
          return render_template('pages/home.html')

      # Check if the artist_id exists
      if Artist.query.get(a_id) is None:
          flash('An error occurred. There is no artist with this id.')
          return render_template('pages/home.html')

      NewShow = Show(venue_id=v_id, artist_id=a_id, start_date=date)
      db.session.add(NewShow)
  except:
      successed = False
      db.session.rollback()
  finally:
      db.session.commit()

  # on successful db insert, flash success
  if successed:
      flash('Show was successfully listed!')
  else:
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Show could not be listed.')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True)
