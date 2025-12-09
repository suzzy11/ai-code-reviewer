class Student:
    def __init__(self, name, marks):
        self.name = name
        self.marks = marks

    def get_average(self):
        return sum(self.marks) / len(self.marks)

    def get_result(self):
        avg = self.get_average()
        if avg >= 40:
            return "Pass"
        return "Fail"


def display_student_result(student):
    print("Name:", student.name)
    print("Average:", student.get_average())
    print("Result:", student.get_result())
