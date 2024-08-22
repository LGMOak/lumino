from translate import translate

#expect: Hola, esto es una prueba.
#works
print(translate('en', 'es', 'Hello, this is a test.'))

#expect: How are you? This is a test.
#works
print(translate(text='你好吗。这是一个测试。'))

#expect: Today Mom died. Or maybe yesterday, I don't know.
#works
print(translate(text="Aujourd'hui Maman est morte. Ou peut-être hier, je ne sais pas"))