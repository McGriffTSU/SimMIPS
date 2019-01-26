import Disassembler
import cache
import sys

class Simulator(object):
  startpc = 96
  currentpc = startpc
  cycle = 1

  def __init__(self, args):
    self.cache = cache.CacheAndPipeline()
    self.dis = self.cache.dis
    for i in range(len(args)):
      if sys.argv[i] == '-o' and i < (len(args) - 1):
        self.outputfilename = args[i + 1] + "_pipeline.txt"

  def run(self):

    outfile = open(self.outputfilename, 'w')
    if len(Disassembler.opcodeStr) != 0:
        cont = True
    else:
        cont = False
    stopping = False
    while cont:
        for j in range(0,2):
          updatebool, vals = self.cache.WB()
          if updatebool:
              self.update(vals)
          if self.cache.stopping:
            cont = self.cache.stop()
        self.cache.PostMEM()
        self.cache.PostALU()
        self.cache.PreMEM_ALU()
        self.cache.IF()
        self.printState(outfile)
        self.cycle += 1
        self.currentpc += 4

  def update(self, values):
      if values[0] == 'ADDI':
        self.addiop(values[1], values[2],values[3])

      if values[0] == 'ADD':
        self.addop(values[1], values[2],values[3])

      if values[0] == 'SUB':
        self.subop(values[1], values[2], values[3])

      if values[0] == 'MUL':
        self.mulop(values[1], values[2], values[3])

      if values[0] == 'MOVZ':
        self.movzop(values[1], values[2], values[3])

      if values[0] == 'SW':
        self.swop(values[1], values[2], values[3])

      if values[0] == 'LW':
        self.lwop(values[1], values[2], values[3])

      if values[0] == 'BLEZ':
        jumpcheck = self.blezop(values[1])
        if jumpcheck:
          immint = values[2].replace(",", '')
          immint = immint.replace('#', '')
          immint = immint.replace(' ', '')
          self.currentpc += (int(immint) + 4)
          i = (self.currentpc - self.startpc) / 4
        else:
          self.currentpc += 4
        self.cycle += 1

      if values[0] == 'BNE':
        jumpcheck = self.bneop(values[1], values[2])
        if jumpcheck:
          immint = values[3].replace(",", '')
          immint = immint.replace('#', '')
          immint = immint.replace(' ', '')
          self.currentpc += (int(immint) + 4)
          i = (self.currentpc - self.startpc) / 4
        else:
          self.currentpc += 4
          i += 1
        self.cycle += 1

      if values[0] == 'SLL':
        reg1int = self.regCheck(values[1])
        reg2int = self.regCheck(values[2])
        if reg1int == 0 and reg2int == 0:
          values[0] = 'NOP'
          values[1] = ''
          values[2] = ''
          values[3] = ''
        else:
          self.sllop(values[1], values[2], values[3])


      if values[0] == 'SRL':
        self.srlop(values[1], values[2], values[3])

      if values[0] == 'J':
        self.currentpc += 4
        self.cycle += 1

        addr = values[1]
        addr = addr.replace('#', '')
        addr = addr.replace('\t', '')

        self.currentpc = int(addr)
        i = (int(addr)-self.startpc)/4

      if values[0] == 'JR':
        regint = self.regCheck(values[1])

        self.currentpc = int(self.cache.registers[regint])
        i = (int(self.currentpc) - self.startpc) / 4

  def addiop(self, reg1, reg2, imm): #ADDI RD = RS + Imm
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)

    immint = imm.strip(",")
    immint = immint.strip(" ")
    immint = immint.replace('#','')

    self.cache.registers[int(reg1int)] = self.cache.registers[int(reg2int)] + int(immint)

  def addop(self, reg1, reg2, reg3): #ADD RD = RS + RT
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    reg3int = self.regCheck(reg3)

    self.cache.registers[int(reg1int)] = self.cache.registers[int(reg2int)] + self.cache.registers[int(reg3int)]

  def subop(self, reg1, reg2, reg3): #SUB RD = RS - RT
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    reg3int = self.regCheck(reg3)

    self.cache.registers[int(reg1int)] = int(self.cache.registers[int(reg2int)]) - int(self.cache.registers[int(reg3int)])

  def mulop(self, reg1, reg2, reg3):
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    reg3int = self.regCheck(reg3)

    self.cache.registers[reg1int] = int(self.cache.registers[reg2int]) * int(self.cache.registers[reg3int])

  def movzop(self, reg1, reg2, reg3):
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    reg3int = self.regCheck(reg3)

    if int(self.cache.registers[reg3int]) == 0:
      self.cache.registers[reg1int] = self.cache.registers[reg2int]

  def swop(self, reg1, offset, reg2): #SW MEM[Offset + RS] = RT
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    offsetint = offset.strip(",")
    memAddr = self.cache.registers[reg2int] + int(offsetint)
    memIndex = self.getMemIndex(memAddr)

    #Check if that memory is mapped yet, if not then we add data up to past that point in memory in 8 word chunks
    if(memIndex >= len(Disassembler.mem)):
      self.dis.expandMem(memIndex)

    #Assign that memory location the value from RT
    Disassembler.mem[memIndex] = self.cache.registers[reg1int]

  def lwop(self, reg1, offset, reg2):  # SW RT = MEM[Offset + RS]
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    offsetint = offset.strip(",")

    memAddr = self.cache.registers[reg2int] + int(offsetint)
    memIndex = self.getMemIndex(memAddr)

    #Assign RT to the value from the memory location
    self.cache.registers[reg1int] = Disassembler.mem[memIndex]

  def blezop(self, reg1):
    reg1int = self.regCheck(reg1)

    if(int(self.cache.registers[reg1int]) <= 0):
      return True
    else:
      return False

  def bneop(self, reg1, reg2):
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)

    if self.cache.registers[reg1int] != self.cache.registers[reg2int]:
      return True
    else:
      return False

  def sllop(self, reg1, reg2, imm): #SLL RD = RT << Imm
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    immint = imm.strip(",")
    immint = immint.replace('#','')


    shiftedbin = self.regtobinary(reg2int)

    finalbin = shiftedbin[int(immint):32]
    for k in range(0,int(immint)):
      finalbin += '0'

    shiftednum = self.dis.stringtonum(finalbin)
    self.cache.registers[reg1int] = int(shiftednum)

  def srlop(self, reg1, reg2, imm): #SLL RD = RT << Imm
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    immint = imm.strip(",")
    immint = immint.replace('#', '')

    rawbin = self.regtobinary(reg2int)

    shiftedbin = ''
    for k in range(0, int(immint)):
      shiftedbin += '0'
    for k in range(0,len(rawbin) - int(immint)):
      shiftedbin += rawbin[k]

    shiftednum = self.dis.stringtonum(shiftedbin)
    self.cache.registers[reg1int] = int(shiftednum)

  def andop(self, reg1, reg2, reg3):
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    reg3int = self.regCheck(reg3)

    rdbin = ''
    rtbin = self.regtobinary(reg2int)
    rsbin = self.regtobinary(reg3int)
    for k in range (0, 32):
      if rtbin[k] == '1':
        if rsbin[k] == '1':
          rdbin += '1'
        else:
          rdbin += '0'
      elif rtbin[k] == '0':
        rdbin += '0'

    rd = self.dis.stringtonum(rdbin)
    self.cache.registers[reg1int] = int(rd)

  def orop(self, reg1, reg2, reg3):
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    reg3int = self.regCheck(reg3)

    rdbin = ''
    rtbin = self.regtobinary(reg2int)
    rsbin = self.regtobinary(reg3int)
    for k in range(0, 32):
      if rtbin[k] == '1':
        rdbin += '1'
      elif rtbin[k] == '0':
        if rsbin[k] == '1':
          rdbin += '1'
        else:
          rdbin += '0'


    rd = self.dis.stringtonum(rdbin)
    self.cache.registers[reg1int] = int(rd)


  def xorop(self, reg1, reg2, reg3):
    reg1int = self.regCheck(reg1)
    reg2int = self.regCheck(reg2)
    reg3int = self.regCheck(reg3)

    rdbin = ''
    rtbin = self.regtobinary(reg2int)
    rsbin = self.regtobinary(reg3int)
    for k in range(0, 32):
      if rtbin[k] == '1':
        if rsbin[k] == '1':
          rdbin += '0'
        else:
          rdbin += '1'
      elif rtbin[k] == '0':
        if rsbin[k] == '1':
          rdbin += '1'
        else:
          rdbin += '0'

    rd = self.dis.stringtonum(rdbin)
    self.cache.registers[reg1int] = int(rd)

  def regtobinary(self, reg): #Takes the register number and returns the 32 bit binary
    tempRTbin = bin(self.cache.registers[reg])
    tempRTbin = tempRTbin[2:]  # To get rid of the 0b at the start from bin(num)

    fillstart = 32 - len(tempRTbin)
    newbin = [0]*32
    j = 0
    for k in range(fillstart, 32, 1):
      newbin[k] = tempRTbin[j]
      j += 1

    finalbin = ''
    for k in range(0, 32):
      finalbin += str(newbin[k])

    return str(finalbin) #Returns 32 bit binary in a 32 character string

  def getMemIndex(self, memAddr): #Converts the MIPS style memory layout to the list index associated with that byte
    memIndex = memAddr - self.dis.memStart #memIndex is now the distance from the start of memory
    memIndex = (memIndex/4)  #memIndex is now the distance from mem[0]
    return memIndex

  def printState(self, out):
    for j in range(20):
      out.write("-"),

    out.write("\nCycle:" + str(self.cycle) + '\n\n')
    out.write(self.cache.BufferstoString())
    out.write("\nRegisters:\n")
    out.write("R00: "),
    for k in range(8):
      out.write("\t" + str(self.cache.registers[k])),

    out.write("\nR08: "),

    for k in range(8, 16, 1):
      out.write("\t" + str(self.cache.registers[k])),

    out.write("\nR16: "),

    for k in range(16, 24, 1):
      out.write("\t" + str(self.cache.registers[k])),

    out.write("\nR24: "),

    for k in range(24, 32, 1):
      out.write("\t" + str(self.cache.registers[k])),

    out.write('\n' + '\n')
    out.write(self.cache.CachetoString())
    out.write("Data")

    for k in range(0, len(Disassembler.mem)):
      linecheck = k%8
      if linecheck == 0:
        out.write('\n')
        linestarter = k*4
        linestarter = linestarter + self.dis.memStart
        out.write(str(linestarter) + ":" + str(Disassembler.mem[k]))
      else:
        out.write("\t" + str(Disassembler.mem[k]))
    out.write('\n')

  def regCheck(self, reg): #Some of these registers should never be used by the programmer, but left them in anyway
    reg = reg.strip("\t")
    reg = reg.strip(",")
    reg = reg.replace(" ", "")
    reg = reg.strip('(')
    reg = reg.strip(')')
    if(reg == 'R1'):
      return int(1)
    elif(reg == 'R2'):
      return int(2)
    elif(reg == 'R3'):
      return int(3)
    elif(reg == 'R4'):
      return int(4)
    elif(reg == 'R5'):
      return int(5)
    elif(reg == 'R6'):
      return int(6)
    elif(reg == 'R7'):
      return int(7)
    elif(reg == 'R8'):
      return int(8)
    elif(reg == 'R9'):
      return int(9)
    elif(reg == 'R10'):
      return int(10)
    elif(reg == 'R11'):
      return int(11)
    elif(reg == 'R12'):
      return int(12)
    elif(reg == 'R13'):
      return int(13)
    elif(reg == 'R14'):
      return int(14)
    elif(reg == 'R15'):
      return int(15)
    elif(reg == 'R16'):
      return int(16)
    elif(reg == 'R17'):
      return int(17)
    elif(reg == 'R18'):
      return int(18)
    elif(reg == 'R19'):
      return int(19)
    elif(reg == 'R20'):
      return int(20)
    elif(reg == 'R21'):
      return int(21)
    elif(reg == 'R22'):
      return int(22)
    elif(reg == 'R23'):
      return int(23)
    elif(reg == 'R24'):
      return int(24)
    elif(reg == 'R25'):
      return int(25)
    elif(reg == 'R26'):
      return int(26)
    elif(reg == 'R27'):
      return int(27)
    elif(reg == 'R28'):
      return int(28)
    elif(reg == 'R29'):
      return int(29)
    elif(reg == 'R30'):
      return int(30)
    elif(reg == 'R31'):
      return int(31)
    else:
      return int(0)

if __name__ == "__main__":
  sim = Simulator(sys.argv)
  sim.run()