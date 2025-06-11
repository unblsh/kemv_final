from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Crime(db.Model):
    __tablename__ = 'spd_crime_data_cleaned_final'
    
    # Using Report_Number as primary key as 'id' column is not in schema
    Report_Number = db.Column('Report Number', db.String(255), primary_key=True)
    Report_DateTime = db.Column('Report DateTime', db.DateTime)
    Offense_ID = db.Column('Offense ID', db.BigInteger)
    Offense_Date = db.Column('Offense Date', db.DateTime)
    NIBRS_Group_AB = db.Column('NIBRS Group AB', db.String(255))
    NIBRS_Crime_Against_Category = db.Column('NIBRS Crime Against Category', db.String(255))
    Offense_Sub_Category = db.Column('Offense Sub Category', db.String(255))
    Shooting_Type_Group = db.Column('Shooting Type Group', db.String(255))
    Block_Address = db.Column('Block Address', db.String(255))
    Latitude = db.Column('Latitude', db.Float)
    Longitude = db.Column('Longitude', db.Float)
    Beat = db.Column('Beat', db.String(255))
    Precinct = db.Column('Precinct', db.String(255))
    Sector = db.Column('Sector', db.String(255))
    Neighborhood = db.Column('Neighborhood', db.String(255))
    Reporting_Area = db.Column('Reporting Area', db.Integer)
    Offense_Category = db.Column('Offense Category', db.String(255))
    NIBRS_Offense_Code_Description = db.Column('NIBRS Offense Code Description', db.String(255))
    NIBRS_offense_code = db.Column('NIBRS_offense_code', db.String(255))

    def __repr__(self):
        return f"<Crime {self.Report_Number}>" 