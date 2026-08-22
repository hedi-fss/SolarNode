"""Main Routes"""
from flask import Blueprint, render_template

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@bp.route('/topology')
def topology():
    return render_template('topology.html')


@bp.route('/analysis')
def analysis():
    return render_template('analysis.html')
