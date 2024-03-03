# Stress-test-prototype
## Описание  
Программа для проверки сервера на скорость обработки запросов и нагрузку.  
Имеет графический интерфейс на базе Tkinter.  
Принимает информацию: url и кол-во запросов, которые будут направлены к серверу.  
После проведения операции, выводит результаты, а именно:  
- время работы;
- результаты запросов;

Построен на двух бесконечных циклах в двух потоках. На главном - графический интерфейс,  
на дочернем - цикл событий, в котором исполняются запросы.  
Потокобезопасность предусмотрена.  
Реализовано пошаговое логирование.  
