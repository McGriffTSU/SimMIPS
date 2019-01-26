import sys

outStr = []
opcodeStr = []  # <type 'list'>: ['Invalid Instruction', 'ADDI', 'SW', 'Invalid Instruction', 'LW', 'BLTZ', 'SLL',...]
validStr = []  # <type 'list'>: ['N', 'Y', 'Y', 'N', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y',.]
instrSpaced = []  # <type 'list'>: ['0 01000 00000 00001 00000 00000 001010', '1 01000 00000 00001 00000 00000 001010',]
instrUnspaced = []
arg1Str = []  # <type 'list'>: ['', '\tR1', '\tR1', '', '\tR1', '\tR1', '\tR10', '\tR3', '\tR4', .....]
arg2Str = []  # <type 'list'>: ['', ', R0', ', 264', '', ', 264', ', #48', ', R1', ', 172', ', 216', ...]'
arg3Str = []  # <type 'list'>: ['', ', #10', '(R0)', '', '(R0)', '', ', #2', '(R10)', '(R10)', '(R0)',...]
mem = []  # <type 'list'>: [-1, -2, -3, 1, 2, 3, 0, 0, 5, -5, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
binMem = []  # <type 'list'>: ['11111111111111111111111111111111', '11111111111111111111111111111110', ...]
class Disassembler(object):
    rawinput = []
    outputfilename = ''
    global outStr
    global opcodeStr
    global validStr
    global instrSpaced
    global instrUnspaced
    global arg1Str
    global arg2Str
    global arg3Str
    global mem
    global binMem
    memStart = -1


    def __init__(self, args):
        for i in range(len(args)):
            if sys.argv[i] == '-i' and i < (len(args) - 1):
                inputfilename = args[i + 1]
                print(inputfilename)
            elif sys.argv[i] == '-o' and i < (len(args) - 1):
                self.outputfilename = args[i + 1] + "_dis.txt"

        inputfile = open(inputfilename, 'r')
        self.rawinput = inputfile.readlines()
        inputfile.close()

    def getLenMem(self):
        return len(mem)

    def expandMem(self, memTarget):
        #Runs until the target memory address is within the memory mapped by mem[]
        binentry = '0'*32
        while(self.getLenMem() <= memTarget):
            #Adds chunks to mem 8 words at a time (8 entries in the list)
            for k in range(0,8):
                mem.append(0)
            for k in range(0,8):
                binMem.append(binentry)



    def stringtoregister(self, code, first=True):
      code = str(int(code, 2))
      if first:
        return '\tR' + code
      else:
        return ', R' + code

    def stringtoimmediate(self, code):
      code = self.stringtonum(code)
      return ', #' + code

    def stringtooffset(self, code):
      code += '00'
      code = self.stringtonum(code)
      return ', #' + code

    def stringtoaddress(self, code):
      code = '0000' + code + '00'
      code = self.stringtonum(code)
      return '\t#' + code

    def wordimmediate(self, code):
      return ', ' + self.stringtonum(code)

    def wordregister(self, code):
      return '(R' + str(int(code, 2)) + ')'

    def stringtonum(self, code):
      x = 0
      i = 0
      for c in code:
        if i == 1:
          x = x * -2 + int(c)
        else:
          x = x * 2 + int(c)
        i += 1
      return str(x)

    def run(self):
      self.fixinput()
      self.findinstruction()
      self.savetofile()

    def fixinput(self):
        i = 0
        for line in self.rawinput:
            instrUnspaced.append(line[0:32])
            tempstring = ''
            for c in line:
                if c == '1' or c == '0':
                    tempstring += c
                    i += 1
                    if i == 1 or i == 6 or i == 11 or i == 16 or i == 21 or i == 26:
                        tempstring += ' '
            instrSpaced.append(tempstring)
            i = 0


    def findinstruction(self):
        breakfound = False
        for code in self.rawinput:
            if breakfound:
                binMem.append(code[0:32])
                mem.append(self.stringtonum(code[0:32]))
            else:
                if code[0] == '0':
                    opcodeStr.append('Invalid Instruction')
                    validStr.append('N')
                    arg1Str.append('')
                    arg2Str.append('')
                    arg3Str.append('')
                else:
                    validStr.append('Y')
                    opcodebin = code[1:6]
                    rs = code[6:11]
                    rt = code[11:16]
                    rd = code[16:21]
                    shamt = code[21:26]
                    funct = code[26:32]
                    immediate = code[16:32]
                    address = code[6:32]
                    if opcodebin == '00000' and funct == '100000':  # ADD rd, rs, rt
                        opcodeStr.append('ADD')
                        arg1Str.append(self.stringtoregister(rd))
                        arg2Str.append(self.stringtoregister(rs, first=False))
                        arg3Str.append(self.stringtoregister(rt, first=False))
                    elif opcodebin == '00000' and funct == '001101':  # BREAK
                        opcodeStr.append('BREAK')
                        arg1Str.append('')
                        arg2Str.append('')
                        arg3Str.append('')
                        breakfound = True
                    elif opcodebin == '01000':  # ADDI rt, rs, immediate
                        opcodeStr.append('ADDI')
                        arg1Str.append(self.stringtoregister(rt))
                        arg2Str.append(self.stringtoregister(rs, first=False))
                        arg3Str.append(self.stringtoimmediate(immediate))
                    elif opcodebin == '00000' and funct == '100010':  # SUB rd, rs, rt
                        opcodeStr.append('SUB')
                        arg1Str.append(self.stringtoregister(rd))
                        arg2Str.append(self.stringtoregister(rs, first=False))
                        arg3Str.append(self.stringtoregister(rt, first=False))
                    elif opcodebin == '00010':  # J target
                        opcodeStr.append('J')
                        arg1Str.append(self.stringtoaddress(address))
                        arg2Str.append('')
                        arg3Str.append('')
                    elif opcodebin == '00000' and funct == '001000':  # JR rs
                        opcodeStr.append('JR')
                        arg1Str.append(self.stringtoregister(rs))
                        arg2Str.append('')
                        arg3Str.append('')
                    elif opcodebin == '00101':  # BNE rs, rt, offset
                        opcodeStr.append('BNE')
                        arg1Str.append(self.stringtoregister(rs))
                        arg2Str.append(self.stringtoregister(rt, first=False))
                        arg3Str.append(self.stringtooffset(immediate))
                    elif opcodebin == '00110':  # BLEZ rs, offset
                        opcodeStr.append('BLEZ')
                        arg1Str.append(self.stringtoregister(rs))
                        arg2Str.append(self.stringtooffset(immediate))
                        arg3Str.append('')
                    elif opcodebin == '01011':  # SW rt, offset(rs)
                        opcodeStr.append('SW')
                        arg1Str.append(self.stringtoregister(rt))
                        arg2Str.append(self.wordimmediate(immediate))
                        arg3Str.append(self.wordregister(rs))
                    elif opcodebin == '00011':  # LW rt, offset(rs)
                        opcodeStr.append('LW')
                        arg1Str.append(self.stringtoregister(rt))
                        arg2Str.append(self.wordimmediate(immediate))
                        arg3Str.append(self.wordregister(rs))
                    elif opcodebin == '00000' and funct == '000000' and code != '00000000000000000000000000000000':  # SLL rd, rt, sa
                        opcodeStr.append('SLL')
                        arg1Str.append(self.stringtoregister(rd))
                        arg2Str.append(self.stringtoregister(rt, first=False))
                        arg3Str.append(self.stringtoimmediate(shamt))
                    elif opcodebin == '00000' and funct == '000010':  # SRL rd, rt, sa
                        opcodeStr.append('SRL')
                        arg1Str.append(self.stringtoregister(rd))
                        arg2Str.append(self.stringtoregister(rt, first=False))
                        arg3Str.append(self.stringtoimmediate(shamt))
                    elif opcodebin == '11100' and funct == '000010':  # MUL rd, rs, rt
                        opcodeStr.append('MUL')
                        arg1Str.append(self.stringtoregister(rd))
                        arg2Str.append(self.stringtoregister(rs, first=False))
                        arg3Str.append(self.stringtoregister(rt, first=False))
                    elif opcodebin == '00000' and funct == '100100':  # AND rd, rs, rt
                        opcodeStr.append('AND')
                        arg1Str.append(self.stringtoregister(rd))
                        arg2Str.append(self.stringtoregister(rs, first=False))
                        arg3Str.append(self.stringtoregister(rt, first=False))
                    elif opcodebin == '00000' and funct == '100101':  # OR rd, rs, rt
                        opcodeStr.append('OR')
                        arg1Str.append(self.stringtoregister(rd))
                        arg2Str.append(self.stringtoregister(rs, first=False))
                        arg3Str.append(self.stringtoregister(rt, first=False))
                    elif opcodebin == '00000' and funct == '100110':  # XOR rd, rs, rt
                        opcodeStr.append('XOR')
                        arg1Str.append(self.stringtoregister(rd))
                        arg2Str.append(self.stringtoregister(rs, first=False))
                        arg3Str.append(self.stringtoregister(rt, first=False))
                    elif opcodebin == '00000' and funct == '001010':  # MOVZ rd, rs, rt
                        opcodeStr.append('MOVZ')
                        arg1Str.append(self.stringtoregister(rd))
                        arg2Str.append(self.stringtoregister(rs, first=False))
                        arg3Str.append(self.stringtoregister(rt, first=False))
                    elif opcodebin == '00000' and funct == '000000' and code == '00000000000000000000000000000000':  # NOP
                        opcodeStr.append('NOP')
                        arg1Str.append('')
                        arg2Str.append('')
                        arg3Str.append('')

    def savetofile(self):
        out = open(self.outputfilename, 'w')
        foundbreak = False
        i = 0
        line = 96
        while foundbreak == False:
            if opcodeStr[i] == 'BREAK':
                text = instrSpaced[i] + '\t' + str(line) + '\t' + opcodeStr[i]
                foundbreak = True
            else:
                if opcodeStr[i] == 'J':
                    text = instrSpaced[i] + '\t' + str(line) + '\t' + opcodeStr[i]  + arg1Str[i]
                else:
                    text = instrSpaced[i] + '\t' + str(line) + '\t' + opcodeStr[i] + arg1Str[i] + arg2Str[i] + arg3Str[i]
            text += '\n'
            out.write(text)
            i += 1
            line += 4
        self.memStart = line
        i = 0
        for code in binMem:
            text = code + '\t' + str(line) + '\t' + str(mem[i]) + '\n'
            i += 1
            line += 4
            out.write(text)
        out.close()


if __name__ == "__main__":
    dis = Disassembler(sys.argv)
    dis.run()

