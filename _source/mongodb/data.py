STUDENTS = """
db.students.insertMany([
  { _id: 2401, name: 'Anuj',    course: 'PG-DBDA', centre: 'Kharghar', marks: 78, skills: ['sql', 'spark'],
    address: { city: 'Pune', pin: '411001' }, scores: [ { sub: 'SQL', m: 82 }, { sub: 'Spark', m: 61 } ] },
  { _id: 2402, name: 'Vineeta', course: 'PG-DBDA', centre: 'Kharghar', marks: 91, skills: ['python', 'hive', 'kafka'],
    address: { city: 'Navi Mumbai', pin: '410210' }, scores: [ { sub: 'SQL', m: 91 }, { sub: 'Spark', m: 88 } ] },
  { _id: 2403, name: 'Aarshvi', course: 'PG-DAC',  centre: 'Juhu',     marks: 84, skills: ['java', 'sql'],
    address: { city: 'Mumbai', pin: '400049' }, scores: [ { sub: 'Java', m: 84 } ] },
  { _id: 2404, name: 'Rohit',   course: 'PG-DAC',  centre: 'Juhu',     marks: 66, skills: [],
    address: { city: 'Thane', pin: '400601' }, scores: [ { sub: 'Java', m: 58 } ] },
  { _id: 2405, name: 'Meera',   course: 'PG-DBDA', centre: 'Kharghar', marks: 78, skills: ['sql', 'python'],
    address: { city: 'Pune', pin: '411038' }, scores: [ { sub: 'SQL', m: 75 } ] },
  { _id: 2406, name: 'Kabir',   course: 'PG-DAI',  centre: 'Juhu',     marks: 72, skills: ['python', 'pytorch'],
    address: { city: 'Mumbai', pin: '400053' }, scores: [ { sub: 'ML', m: 72 } ] },
  { _id: 2407, name: 'Sana',    course: 'PG-DAI',  centre: 'Kharghar', marks: 88, skills: ['python', 'sql'],
    address: { city: 'Navi Mumbai', pin: '410206' }, scores: [ { sub: 'ML', m: 88 } ] },
  { _id: 2408, name: 'Dev',     course: 'PG-DAC',  centre: 'Juhu',     marks: 59, skills: ['java'],
    address: { city: 'Mumbai', pin: '400058' }, scores: [ { sub: 'Java', m: 59 } ] }
])
"""

SMALL = """
db.students.insertMany([
  { _id: 2401, name: 'Anuj',    course: 'PG-DBDA', marks: 78, skills: ['sql', 'spark'] },
  { _id: 2402, name: 'Vineeta', course: 'PG-DBDA', marks: 91, skills: ['python', 'hive'] },
  { _id: 2403, name: 'Aarshvi', course: 'PG-DAC',  marks: 84, skills: ['java'] },
  { _id: 2404, name: 'Rohit',   course: 'PG-DAC',  marks: 66, skills: [] }
])
"""
