import os
from flask import Flask, render_template, request, redirect, jsonify
from utils.db import db
from models.ipl_player import IPLPlayer  # Ensure correct import

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/IPL.db'  # Fix SQLite issue for Render
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize the database
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    players = IPLPlayer.query.all()
    return render_template('index.html', content=players)


@app.route('/hello')
def index():
    return "hello world"

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        email = request.form.get('email').strip()
        message = request.form.get('message').strip()

        if not name or not email or not message:
            return jsonify({"status": "error", "message": "All fields are required."}), 400

        new_contact = Contact(name=name, email=email, message=message)
        db.session.add(new_contact)
        try:
            db.session.commit()
            return jsonify({"status": "success", "message": "Thank you for contacting us!"})
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "An error occurred while saving your data."}), 500

    return render_template('contact.html')


@app.route('/matches')
def matches():
    matches = Matches.query.all()
    return render_template('matches.html', matches=matches)


@app.route('/news')
def news():
    return render_template('news.html')


@app.route('/players')
def players():
    players = IPLPlayer.query.all()
    return render_template('players_list.html', players=players)


@app.route('/points_table')
def points_table():
    matches = Matches.query.all()
    points_table = {}

    for match in matches:
        for team in [match.team1, match.team2]:
            if team not in points_table:
                points_table[team] = {'matches_played': 0, 'wins': 0, 'losses': 0, 'points': 0}

        points_table[match.team1]['matches_played'] += 1
        points_table[match.team2]['matches_played'] += 1

        if match.match_winner == match.team1:
            points_table[match.team1]['wins'] += 1
            points_table[match.team1]['points'] += 2
            points_table[match.team2]['losses'] += 1
        elif match.match_winner == match.team2:
            points_table[match.team2]['wins'] += 1
            points_table[match.team2]['points'] += 2
            points_table[match.team1]['losses'] += 1

    sorted_points_table = sorted(points_table.items(), key=lambda x: (-x[1]['points'], -x[1]['wins']))

    return render_template('points_table.html', points_table=sorted_points_table)


@app.route('/submit', methods=['POST'])
def submit():
    player = IPLPlayer(
        player_id=request.form['player_id'],
        player_name=request.form['player_name'],
        team=request.form['team'],
        matches_played=request.form['matches_played'],
        runs_scored=request.form.get('runs_scored', 0),
        wickets_taken=request.form.get('wickets_taken', 0),
        image=request.form.get('image', '')
    )
    db.session.add(player)
    db.session.commit()
    return redirect('/players')


@app.route('/update/<int:player_id>', methods=['PUT'])
def update_player(player_id):
    player = IPLPlayer.query.get_or_404(player_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    player.player_name = data.get('player_name', player.player_name)
    player.team = data.get('team', player.team)
    player.matches_played = data.get('matches_played', player.matches_played)
    player.runs_scored = data.get('runs_scored', player.runs_scored)
    player.wickets_taken = data.get('wickets_taken', player.wickets_taken)
    player.image = data.get('image', player.image)

    db.session.commit()
    return jsonify({'message': 'Player updated successfully'})


@app.route('/delete/<int:player_id>', methods=['DELETE'])
def delete_player(player_id):
    player = IPLPlayer.query.get(player_id)
    if not player:
        return jsonify({'message': 'Player not found'}), 404

    try:
        db.session.delete(player)
        db.session.commit()
        return jsonify({'message': 'Player deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'An error occurred: {e}'}), 500


@app.route('/teams', methods=['GET'])
def view_teams():
    teams = Teams.query.all()
    return render_template('teams.html', teams=teams)


@app.route('/submit_team', methods=['POST'])
def submit_team():
    team = Teams(
        team_name=request.form['team_name'],
        team_captain=request.form['team_captain'],
        championships_won=request.form['championships_won']
    )
    db.session.add(team)
    db.session.commit()
    return redirect('/teams')


@app.route('/update_team/<int:team_id>', methods=['POST'])
def update_team(team_id):
    team = Teams.query.get_or_404(team_id)
    team.team_name = request.form['team_name']
    team.team_captain = request.form['team_captain']
    team.championships_won = request.form['championships_won']
    db.session.commit()
    return jsonify({'message': 'Team updated successfully'})


@app.route('/delete_team/<int:team_id>', methods=['DELETE'])
def delete_team(team_id):
    team = Teams.query.get(team_id)
    if not team:
        return jsonify({'message': 'Team not found'}), 404

    try:
        db.session.delete(team)
        db.session.commit()
        return jsonify({'message': 'Team deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'An error occurred: {e}'}), 500


@app.route('/team/<team_name>', methods=['GET'])
def team_details(team_name):
    players = IPLPlayer.query.filter_by(team=team_name).all()
    return render_template('team_details.html', team_name=team_name, players=players)


# ✅ Ensure proper deployment on Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Dynamic port handling
    app.run(host='0.0.0.0', port=port)
