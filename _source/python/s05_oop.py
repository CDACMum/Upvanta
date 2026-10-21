from build import *

SECTION = dict(level='intermediate', title='Object-Oriented Python', questions=[

# ------------------------------------------------------------------ 27
Q('What are classes and objects? Explain __init__ and self', 'Classes & Objects', minutes=6, cards=[
    definition(
        defbox('A <strong>class</strong> is a blueprint that defines attributes (data) and methods (behaviour). An '
               '<strong>object</strong> (instance) is a concrete thing created from that blueprint.',
               '<code>__init__</code> is the <strong>initialiser</strong>, called automatically after a new object is '
               'created, to set its attributes. <code>self</code> is the reference to the current instance — Python passes '
               'it automatically as the first argument of every instance method.'),
        tags('class', 'object', '__init__', 'self', 'Instance Attribute', 'Class Attribute'),
    ),
    example(
        pyrun("""
class Student:
    institute = "C-DAC"                  # class attribute: shared by all

    def __init__(self, student_id, name, marks=None):
        self.student_id = student_id     # instance attributes: per object
        self.name = name
        self.marks = marks or []

    def add_mark(self, mark):
        self.marks.append(mark)

    def average(self):
        return sum(self.marks) / len(self.marks) if self.marks else 0.0

asha = Student(101, "Asha")
rohit = Student(102, "Rohit", [70, 80])
asha.add_mark(90); asha.add_mark(84)

print(asha.name, asha.average(), rohit.average())
print(asha.institute, Student.institute)
print(vars(asha))
print(Student.average(asha))             # what asha.average() really does
"""),
        title='Example'),
    crossq(
        ('Is __init__ a constructor?',
         'Strictly, the constructor is <code>__new__</code>, which creates the object; <code>__init__</code> initialises it. In interviews "constructor" usually refers to <code>__init__</code> — mention both.'),
        ('Is "self" a keyword?',
         'No, only a strong convention. Any name works, but always use <code>self</code>.'),
        ('Class attribute vs instance attribute — what is the trap?',
         'A mutable class attribute (e.g. <code>items = []</code> at class level) is shared by every instance. Initialise per-object data in <code>__init__</code>.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What is the difference between instance methods, class methods and static methods?', 'Instance vs Class vs Static Methods', minutes=6, cards=[
    definition(
        table(['Type', 'Decorator', 'First argument', 'Can access', 'Typical use'], [
            ['Instance method', '(none)', 'self', 'Instance + class data', 'Behaviour of one object'],
            ['Class method', '@classmethod', 'cls', 'Class data (not a specific instance)', 'Alternative constructors / factories'],
            ['Static method', '@staticmethod', '(none)', 'Neither, only its arguments', 'Utility function grouped with the class'],
        ]),
        tags('@classmethod', '@staticmethod', 'cls', 'Factory Method', 'Alternative Constructor'),
    ),
    example(
        pyrun("""
from datetime import date

class Employee:
    count = 0

    def __init__(self, name, salary):
        self.name, self.salary = name, salary
        Employee.count += 1

    def annual(self):                         # instance method
        return self.salary * 12

    @classmethod
    def from_csv(cls, line):                  # alternative constructor
        name, salary = line.split(",")
        return cls(name.strip(), int(salary))

    @staticmethod
    def is_working_day(d):                    # utility, no self / cls
        return d.weekday() < 5

e1 = Employee("Asha", 60000)
e2 = Employee.from_csv("Rohit, 55000")
print(e2.name, e2.annual(), Employee.count)
print(Employee.is_working_day(date(2026, 10, 10)))   # a Saturday
"""),
        title='Example'),
    crossq(
        ('Why use cls() instead of Employee() in a class method?',
         'So subclasses work: <code>Manager.from_csv(...)</code> then returns a Manager, not an Employee.'),
        ('When would you use a static method rather than a module-level function?',
         'When the helper is conceptually part of the class\'s API and is used mainly by it. Otherwise a plain function is perfectly Pythonic.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('Explain inheritance, super() and Method Resolution Order (MRO)', 'Inheritance & MRO', minutes=7, cards=[
    definition(
        defbox('<strong>Inheritance</strong> lets a child class reuse and extend a parent class. Python supports single, '
               'multilevel, hierarchical and <strong>multiple</strong> inheritance.',
               '<code>super()</code> calls the next method in the <strong>Method Resolution Order (MRO)</strong> — the '
               'order in which Python searches classes for an attribute. Python computes it with the <strong>C3 '
               'linearization</strong> algorithm.'),
        tags('Inheritance', 'super()', 'MRO', 'C3 Linearization', 'Multiple Inheritance', 'Method Overriding'),
    ),
    example(
        pyrun("""
class Source:
    def __init__(self, name):
        self.name = name
    def read(self):
        return f"reading from {self.name}"

class DatabaseSource(Source):
    def __init__(self, name, table):
        super().__init__(name)             # reuse parent initialisation
        self.table = table
    def read(self):                        # override
        return super().read() + f" (table={self.table})"

src = DatabaseSource("mysql-prod", "orders")
print(src.read())
print(isinstance(src, Source), issubclass(DatabaseSource, Source))

# Multiple inheritance & MRO (diamond)
class A:
    def who(self): return "A"
class B(A):
    def who(self): return "B -> " + super().who()
class C(A):
    def who(self): return "C -> " + super().who()
class D(B, C):
    def who(self): return "D -> " + super().who()

print(D().who())
print([cls.__name__ for cls in D.__mro__])
"""),
        note('In the diamond, <code>super()</code> in B calls <strong>C</strong>, not A — it follows the MRO of the actual object (D, B, C, A, object), so A runs only once.'),
        title='Example'),
    crossq(
        ('What is a mixin?',
         'A small class that adds one piece of behaviour (e.g. <code>JsonSerializableMixin</code>, <code>LoggingMixin</code>) and is combined with other classes via multiple inheritance. It is not meant to be instantiated alone.'),
        ('Composition vs inheritance?',
         '"Has-a" vs "is-a". Prefer composition (an object holds other objects) when the relationship is not a true specialisation — it is more flexible and avoids deep, fragile hierarchies.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('How is encapsulation done in Python? Explain _, __ and @property', 'Encapsulation & @property', minutes=6, cards=[
    definition(
        defbox('Python has no truly private members. Encapsulation is by <strong>convention</strong>:'),
        table(['Naming', 'Meaning'], [
            ['<code>name</code>', 'Public'],
            ['<code>_name</code>', '"Internal — please don\'t use from outside" (convention only)'],
            ['<code>__name</code>', '<strong>Name mangling</strong>: renamed to <code>_ClassName__name</code> to avoid clashes in subclasses'],
            ['<code>__name__</code>', 'Dunder / special names reserved for Python — do not invent your own'],
        ]),
        p('<code>@property</code> turns a method into a managed attribute, so you can add validation or computed values '
          'while callers still use simple attribute syntax.'),
        tags('Encapsulation', 'Name Mangling', '@property', 'Getter', 'Setter', 'Validation'),
    ),
    example(
        pyrun("""
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self._balance = balance          # internal by convention
        self.__pin = "1234"              # name-mangled

    @property
    def balance(self):                   # read access: acc.balance
        return self._balance

    @balance.setter
    def balance(self, value):            # write access with validation
        if value < 0:
            raise ValueError("balance cannot be negative")
        self._balance = value

acc = BankAccount("Asha", 5000)
acc.balance = 7000
print(acc.balance)

try:
    acc.balance = -10
except ValueError as e:
    print("ValueError:", e)

print(hasattr(acc, "__pin"), acc._BankAccount__pin)   # mangled, not secret
"""),
        title='Example'),
    crossq(
        ('Why use @property instead of get_balance()/set_balance()?',
         'You can start with a plain public attribute and later add validation without changing any calling code. It is the Pythonic replacement for Java-style getters and setters.'),
        ('Is name mangling a security feature?',
         'No. It only prevents accidental name clashes in subclasses; the attribute is still reachable as <code>_ClassName__attr</code>.'),
    ),
]),

# ------------------------------------------------------------------ 31
Q('Explain polymorphism, duck typing and abstract base classes', 'Polymorphism & ABCs', minutes=7, cards=[
    definition(
        defbox('<strong>Polymorphism</strong>: the same interface (method name) behaves differently depending on the object.',
               '<strong>Duck typing</strong>: "if it walks like a duck and quacks like a duck, it\'s a duck" — Python cares '
               'whether an object <em>has</em> the needed methods, not what class it is.',
               'An <strong>Abstract Base Class (ABC)</strong> defines methods that subclasses <strong>must</strong> implement; '
               'it cannot be instantiated itself.'),
        tags('Polymorphism', 'Duck Typing', 'ABC', '@abstractmethod', 'Interface', 'Protocol'),
    ),
    example(
        pyrun("""
from abc import ABC, abstractmethod

class Extractor(ABC):
    @abstractmethod
    def extract(self):
        ...

class CsvExtractor(Extractor):
    def extract(self):
        return ["row from csv"]

class ApiExtractor(Extractor):
    def extract(self):
        return ["row from api"]

def run_pipeline(extractors):
    for e in extractors:                 # polymorphism: same call, different behaviour
        print(type(e).__name__, "->", e.extract())

run_pipeline([CsvExtractor(), ApiExtractor()])

try:
    Extractor()
except TypeError as err:
    print("TypeError:", err)

class S3Extractor:                       # NOT a subclass ...
    def extract(self):
        return ["row from s3"]
run_pipeline([S3Extractor()])            # ... still works: duck typing
"""),
        title='Example: Pluggable Extractors'),
    crossq(
        ('Does Python support method overloading?',
         'Not by signature like Java — a second <code>def</code> with the same name replaces the first. Use default arguments, <code>*args</code>, or <code>functools.singledispatch</code> for type-based dispatch.'),
        ('What is operator overloading?',
         'Defining dunder methods so operators work on your objects: <code>__add__</code> for <code>+</code>, <code>__eq__</code> for <code>==</code>, <code>__lt__</code> for <code>&lt;</code>.'),
        ('ABC vs typing.Protocol?',
         'An ABC requires explicit inheritance and checks at instantiation. A <code>Protocol</code> (3.8+) describes the required methods for static type checkers — "static duck typing" without inheritance.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('What are dunder (magic) methods? Explain __str__ vs __repr__', 'Dunder Methods', minutes=6, cards=[
    definition(
        defbox('<strong>Dunder</strong> (double underscore) methods let your classes plug into Python\'s built-in behaviour '
               '— printing, comparison, arithmetic, len(), iteration, <code>with</code>, and more.'),
        table(['Method', 'Triggered by'], [
            ['__init__', 'Creating an object'],
            ['__str__', 'print(obj), str(obj) — readable, for end users'],
            ['__repr__', 'repr(obj), the REPL, inside lists — unambiguous, for developers'],
            ['__eq__, __lt__, …', '==, &lt;, sorting'],
            ['__hash__', 'Use as dict key / in set'],
            ['__len__', 'len(obj)'],
            ['__getitem__', 'obj[key], also makes it iterable'],
            ['__iter__, __next__', 'for loops'],
            ['__contains__', 'x in obj'],
            ['__call__', 'obj() — callable objects'],
            ['__enter__, __exit__', 'with statement'],
        ]),
        tags('Dunder Methods', '__str__', '__repr__', '__eq__', '__len__', 'Operator Overloading'),
    ),
    example(
        pyrun("""
class Batch:
    def __init__(self, name, rows):
        self.name, self.rows = name, list(rows)

    def __repr__(self):
        return f"Batch(name={self.name!r}, rows={len(self.rows)})"

    def __str__(self):
        return f"{self.name} with {len(self.rows)} rows"

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        return self.rows[i]

    def __add__(self, other):
        return Batch(f"{self.name}+{other.name}", self.rows + other.rows)

    def __eq__(self, other):
        return isinstance(other, Batch) and self.rows == other.rows

b1, b2 = Batch("jan", [1, 2]), Batch("feb", [3])
print(b1)                 # __str__
print([b1, b2])           # __repr__ inside a list
print(len(b1 + b2), (b1 + b2)[2], 2 in b1)
print(b1 == Batch("x", [1, 2]))
"""),
        title='Example'),
    crossq(
        ('If only one of __str__/__repr__ is defined, which?',
         'Define <code>__repr__</code> — <code>str()</code> falls back to it when <code>__str__</code> is missing, but not the other way round.'),
        ('Why does defining __eq__ make objects unhashable?',
         'Python sets <code>__hash__ = None</code> when you define <code>__eq__</code> without <code>__hash__</code>, because equal objects must have equal hashes. Define <code>__hash__</code> too (based on the same immutable fields) if instances should be dict keys.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('What are dataclasses?', 'Dataclasses', minutes=5, cards=[
    definition(
        defbox('<code>@dataclass</code> (Python 3.7+) automatically generates <code>__init__</code>, <code>__repr__</code> '
               'and <code>__eq__</code> (and optionally ordering and hashing) from class-level type-annotated fields. '
               'It removes boilerplate for classes that mainly hold data.'),
        tags('@dataclass', 'field', 'frozen', 'Boilerplate', 'Type Hints', 'pydantic'),
    ),
    example(
        pyrun("""
from dataclasses import dataclass, field, asdict
from datetime import date

@dataclass(order=True)
class Order:
    order_id: int
    customer: str
    amount: float = 0.0
    items: list = field(default_factory=list)     # safe mutable default
    order_date: date = field(default_factory=date.today, compare=False)

o1 = Order(5001, "Asha", 1499.0, ["P1"])
o2 = Order(5001, "Asha", 1499.0, ["P1"])
print(o1 == o2)
print(sorted([Order(3, "Z"), Order(1, "A")])[0].order_id)
print({k: v for k, v in asdict(o1).items() if k != "order_date"})

@dataclass(frozen=True)
class Config:
    host: str
    port: int = 3306

cfg = Config("db.local")
try:
    cfg.port = 5432
except Exception as e:
    print(type(e).__name__)
print(hash(cfg) == hash(Config("db.local")))
"""),
        title='Example'),
    crossq(
        ('Dataclass vs namedtuple vs pydantic model?',
         '<strong>namedtuple</strong>: immutable, tuple-like, minimal. <strong>dataclass</strong>: mutable by default, '
         'methods and defaults, no runtime validation. <strong>pydantic</strong>: validates and converts types at runtime — '
         'ideal for API payloads and configs in pipelines.'),
        ('Why default_factory instead of items: list = []?',
         'A plain mutable default would be shared by all instances (the same trap as question 17); dataclasses actually raise an error for it. default_factory builds a fresh list per object.'),
    ),
]),

])
