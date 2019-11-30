
from jinja2 import DictLoader, Environment

import argparse
import json
import importlib
import random
import string



HEADER = """

#pragma once
#include <rapidjson/rapidjson.h>
#include <rapidjson/writer.h>
#include <rapidjson/reader.h>

#include <iostream>
#include <string>
#include <vector>
#include <map>

struct {{ schema["title"] }}
{
    {{ schema["title"] }}()
    {
        {%- for property_name, property_dict  in schema["properties"].items() %}
        PropertyMap["{{ property_dict["title"] }}"] = &{{ property_dict["title"] }};
        {%- endfor %}
    }


    template<typename OutputStream>
    void Write(rapidjson::Writer<OutputStream>& writer)
    {
        writer.StartObject();
        {%- for property_name, property_dict  in schema["properties"].items() %}
        writer.Key("{{ property_dict["title"] }}");
        {{ get_writer_code(property_dict) }} 
        {%- endfor %}
        writer.EndObject();
    }

    {%- for property_name, property_dict  in schema["properties"].items() %}
    {{ get_property_type(property_dict) }} {{ property_dict["title"] }};
    {%- endfor %}

    bool operator==(const {{ schema["title"] }}& rhs) const
    {
        bool equals = true;
        {%- for property_name, property_dict  in schema["properties"].items() %}
        equals =  equals && {{ property_dict["title"] }} == rhs.{{ property_dict["title"] }};
        {%- endfor %}
        return equals;

    }

    std::map<std::string, void*> PropertyMap;
};

struct {{ schema["title"] }}Handler
{
    {{ schema["title"] }}Handler( {{ schema["title"] }}* ParseObject)
    {
        Object = ParseObject;
    }

    bool Null() { std::cout << "Null()" << std::endl; return true; }

    bool Bool(bool b) 
    { 
        if(!CurrentProperty)
        {
            return false;
        }

        bool& PropertyBool = *reinterpret_cast<bool*>(CurrentProperty);
        PropertyBool = b;
        
        CurrentProperty = nullptr;

        return true;
    }

    bool Int(int i)
    {
        if(!CurrentProperty)
        {
            return false;
        }

        int32_t& PropertyInt = *reinterpret_cast<int32_t*>(CurrentProperty);
        PropertyInt = i;
        
        CurrentProperty = nullptr;

        return true;
    }

    bool Uint(unsigned u) 
    { 
        if(!CurrentProperty)
        {
            return false;
        }

        uint32_t& PropertyUInt = *reinterpret_cast<uint32_t*>(CurrentProperty);
        PropertyUInt = u;
        
        CurrentProperty = nullptr;

        return true;
    }

    bool Int64(int64_t i) { std::cout << "Int64(" << i << ")" << std::endl; return true; }
    bool Uint64(uint64_t u) { std::cout << "Uint64(" << u << ")" << std::endl; return true; }

    bool Double(double d) 
    {
        if(!CurrentProperty)
        {
            return false;
        }

        double& PropertyDouble = *reinterpret_cast<double*>(CurrentProperty);
        PropertyDouble = d;
        
        CurrentProperty = nullptr;

        return true;
    }
    
    bool RawNumber(const char* str, rapidjson::SizeType length, bool copy) 
    { 
        std::cout << "Number(" << str << ", " << length << ", " << "boolalpha" << copy << ")" << std::endl;
        return true;
    }

    bool String(const char* str, rapidjson::SizeType length, bool copy) 
    { 
        if(!CurrentProperty)
        {
            return false;
        }

        std::string& PropertyString = *reinterpret_cast<std::string*>(CurrentProperty);
        PropertyString = std::string(str, length);

        CurrentProperty = nullptr;
     
        return true;
    }

    bool Key(const char* str, rapidjson::SizeType length, bool copy) 
    {
        const auto it = Object->PropertyMap.find(str);

        if(it != Object->PropertyMap.end())
        {
            CurrentProperty = it->second;
            return true;
        }
        else
        {
            return false;
        }
    }

    bool StartObject() { std::cout << "StartObject()" << std::endl; return true; }
    bool EndObject(rapidjson::SizeType memberCount) { std::cout << "EndObject(" << memberCount << ")" << std::endl; return true; }
    bool StartArray() { std::cout << "StartArray()" << std::endl; return true; }
    bool EndArray(rapidjson::SizeType elementCount) { std::cout << "EndArray(" << elementCount << ")" << std::endl; return true; }

    {{ schema["title"] }}* Object = nullptr;
    void* CurrentProperty = nullptr;
};

"""

TEST = """

#include "Json{{ schema["title"] }}.h"

int main(int argc, char** argv)
{
    {{ schema["title"] }} WriteObject;
    {%- for property_name, property_dict  in schema["properties"].items() %}
    WriteObject.{{ property_dict["title"] }} = {{ random_function_map[property_dict["type"]]() }};
    {%- endfor %}
    {{ schema["title"] }} ReadObject;

    rapidjson::StringBuffer StringBuf;
    rapidjson::Writer<rapidjson::StringBuffer> Writer(StringBuf);
    WriteObject.Write(Writer);

    {{ schema["title"] }}Handler Handler(&ReadObject);
    rapidjson::Reader Reader;
    rapidjson::StringStream StringStream(StringBuf.GetString());
    Reader.Parse(StringStream, Handler);

    bool Equals = WriteObject == ReadObject;
    if(!Equals)
    {
        fprintf(stderr, "Objects not equals.");
        return 1;
    }

    return 0;
}
"""

writer_function_map = {
    "integer" : "Int",
    "number" : "Double",
    "boolean" : "Bool"
}

def get_writer_code(prop : dict, title = None):
    type_name = prop["type"]
    if title == None: title = prop["title"]

    if type_name in writer_function_map:
        return "writer." + writer_function_map[type_name] + "(" + title + ");"
    elif type_name == "string":
        return "writer.String("+ prop["title"] + ".c_str());"
    elif type_name == "array":
        write_array =  "writer.StartArray();\n"
        write_array += "        for( auto it = " + title + ".begin(); it != " + title + ".end(); ++it)\n"
        write_array += "        {\n"
        write_array += "            " + get_writer_code(prop["items"], "(*it)") + "\n"
        write_array += "        }\n"
        write_array += "        writer.EndArray(" + title + ".size());"
        return write_array

    return None

    

# types
basic_type_map = { 
    "integer" : "int32_t",
    "string" : "std::string",
    "number" : "double",
    "boolean" : "bool"
}

def get_property_type(prop : dict):
    type_name = prop["type"]
    if type_name in basic_type_map:
        return basic_type_map[type_name]
    if type_name == "array":
        return "std::vector<" + get_property_type(prop["items"]) + ">"

    return "void" 

# test methods
def random_string(len=10):
    letters = string.ascii_lowercase
    s = ''.join(random.choice(letters) for i in range(len))
    return "\"" + s + "\""

def random_int():
    return random.randint(0,1024)

def random_double():
    return random.randint(0,1024)

def random_bool():
    return random.choice(["true", "false"])

def random_array():
    return "{}"

random_function_map = {
    "integer" : random_int,
    "string" : random_string,
    "number" : random_double,
    "boolean" : random_bool,
    "array" : random_array
}

templates = Environment(loader=DictLoader(globals()))

def generate_header(schema_class):
    print(schema_class.schema_json())

    template = templates.get_template("HEADER")
    schema =  json.loads(schema_class.schema_json())
    
    rendered = template.render( 
        { "schema" : schema,
          "get_property_type" : get_property_type,
          "get_writer_code" : get_writer_code,
        } 
    )
    header = open("Json"+schema["title"]+".h", "w+")
    header.write(rendered)
    header.close()

def generate_test(schema_class):

    template = templates.get_template("TEST")
    schema =  json.loads(schema_class.schema_json())
    
    rendered = template.render( 
        { "schema" : schema,
          "get_property_type" : get_property_type,
          "random_function_map" : random_function_map
        } 
    )
    test = open("Json"+schema["title"]+"Test.cpp", "w+")
    test.write(rendered)
    test.close()

if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", help="Package that needs to be loaded to access your type")
    parser.add_argument("--typename", help="Name of the type to generate code from.")

    args = parser.parse_args();

    module = None

    if args.package != None:
        print("Loading %s" %(args.package))
        module = importlib.import_module(args.package)

    if args.typename != None:
        generate_header(getattr(module,args.typename))
        generate_test(getattr(module,args.typename))
    
        


