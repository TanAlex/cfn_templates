class Singleton:
    
    def __init__(self, cls):
        self._cls = cls

    def Instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._cls()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._cls)

# REF: https://medium.com/better-programming/singleton-in-python-5eaa66618e3d
# Usage
# @Singleton
# class DBConnection(object):

#     def __init__(self):
#         """Initialize your database connection here."""
#         pass

#     def __str__(self):
#         return 'Database connection object'