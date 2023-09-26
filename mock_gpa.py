from controls import Utils

class_details = {
    "CLASSES": [
        {
            "CLASS_NAME": "College Physics",
            "LETTER_GRADE": "A",
        },
        {
            "CLASS_NAME": "Honors",
            "LETTER_GRADE": "A",
        },
        {
            "CLASS_NAME": "Honors",
            "LETTER_GRADE": "B",
        },
        {
            "CLASS_NAME": "Honors",
            "LETTER_GRADE": "A",
        },
        {
            "CLASS_NAME": "Honors",
            "LETTER_GRADE": "B",
        },
        {
            "CLASS_NAME": "Honors",
            "LETTER_GRADE": "A",
        },        {
            "CLASS_NAME": "AP",
            "LETTER_GRADE": "A",
        }

    ]
}

print(Utils.gpa_calculator(class_details))

