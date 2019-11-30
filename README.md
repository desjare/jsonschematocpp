# jsonschematocpp

Tool to generate rapidjson C++ classes, reader, writer and tests from pydantic schema python classes. The goal is to ease the development of C++ REST clients.

The tool generates C++ classes that can be compiled with [rapidjson](https://rapidjson.org) based on [pydantic](https://github.com/samuelcolvin/pydantic) schema python files. For now only basic types are supported:
* integer
* string
* number (double)
* boolean
