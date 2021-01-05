import json
from bl.base import StkEncoder

# class StkEncoder(json.JSONEncoder): # --> bl.base.StkEncoder
#     def default(self, obj):
#         if hasattr(obj, '_json_encode'):
#             return obj._json_encode()
#         else:
#             return json.JSONEncoder.default(self, obj)
# 
# def stk_jsonify(obj): # --> bl.base.StkEncoder.jsonify
#     return json.dumps(obj, cls=StkEncoder) 


# -- test code --
class Base:
    def to_json(self):
        return json.dumps(self, cls=StkEncoder) 
    def _json_encode(self):
        return self.__dict__

    
class Test(Base):
    def __init__(self):
        self.name = "Abc"
    def x_json_encode(self):
        return dict(name=self.name)
    
class Test2(Base):
    def __init__(self):
        self.name = "xAbc"
        self.item = Test()
    def x_json_encode(self):
        return dict(name=self.name, item=self.item)

if __name__ == "__main__":
    test = Test()
    s = test.to_json()
    s = StkEncoder.jsonify(test)
    print(s)    
    
    test2 = Test2()
    s = test2.to_json()
    s = StkEncoder.jsonify(test2)
    print(s)    
    
    test3 = 1
    s = StkEncoder.jsonify(test3)
    print(s)    
    
    test4 = dict(test=test,test2=test2)
    s = StkEncoder.jsonify(test4)
    print(s)    
    
    #s = json.dumps(test)