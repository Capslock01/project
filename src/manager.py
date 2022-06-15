import datetime
from flask import render_template
from flask import render_template
from flask import g
from src import app, db
from src.login import require_login


@app.route('/app')
@require_login()
def manager():
    """Handles the main app function."""

    # Get user's projects. E."end" is needed to determine whether project is running or paused
    # COALESCE("end", NOW()) makes running projects show current time when page is refreshed
    query = """SELECT
                   P.id, P.name, C.name, P.state,
                   (SELECT
                        SUM(EXTRACT(EPOCH
                        FROM COALESCE("end", NOW())-start))*interval '1 sec' as diff
                    FROM entry WHERE project_id = P.id
                    ) as time
               FROM
                   project P, company C
               WHERE
                   P.company_id = C.id AND P.user_id=:uid
               ORDER BY
                   P.state DESC, P.id DESC"""
    projects = db.session.execute(query, {'uid': g.user}).fetchall()
    return render_template(
        'manager.html',
        projects = projects,
        timeformat = timeformat # Needed to format times in template
    )


@app.template_filter()
def timeformat(timedelta: datetime.timedelta) -> str:
    """Format timedelta object to HH:MM:SS.
    
    Timedelta shows days, this converts them into hours.
    """

    if timedelta is None:
        timedelta = datetime.timedelta(seconds = 0)
    timedelta = int(timedelta.total_seconds())
    hours = timedelta // 3600
    minutes = timedelta // 60 - (hours * 60)
    seconds = timedelta - (minutes*60) - (hours*3600)
    return f'{hours:02}:{minutes:02}:{seconds:02}'
