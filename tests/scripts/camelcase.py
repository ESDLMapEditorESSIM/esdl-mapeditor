from utils import utils

if __name__ == "__main__":

    # print(utils.unCamelCase('Test'))
    # print(utils.unCamelCase('test'))
    # print(utils.unCamelCase('TEST'))
    # print(utils.unCamelCase('TEst'))

    print(utils.camelCaseToWords("CamelCase"))
    print(utils.camelCaseToWords("Camelcase"))
    print(utils.camelCaseToWords("CAMelcase"))
    print(utils.camelCaseToWords("CAMelCase"))
    print(utils.camelCaseToWords("camelCase"))