import Disassembler
import sys
import re

class CacheAndPipeline(object):
    def __init__(self):
        self.registers = [0] * 32  # Register ($0-$31) values
        self.cache_mem = [[[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]], [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
                         [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]], [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]] # valid, dirty, tag, instr1, instr 2
        self.pre_issue = [[''], [''], [''], ['']]
        self.pre_alu = [[''], ['']]
        self.post_alu = [['']]
        self.pre_mem = [[''], ['']]
        self.post_mem = [['']]
        self.mem_holder = ['']
        self.IFholder = [[''], ['']]
        self.instrholder = [[''], ['']]
        self.instr = 0
        self.stopping = False
        self.LRUbit = [0]*4
        self.holderset1 = 0
        self.holderset2 = 0
        self.holdertag1 = 0
        self.holdertag2 = 0
        self.issued = 0
        self.SWI = 0
        self.dis = Disassembler.Disassembler(sys.argv)
        self.hazard = False
        self.dis.run()
    def shuffle(self, ar, filler=[''], pos=0):
        if pos == 0:
            ar.append(filler)
            return ar[0], ar[1:len(ar)]
        else:
            temp = []
            for i in range(0, len(ar)):
                if i != pos:
                    temp.append(ar[i])
            temp.append([''])
            return ar[pos], temp

    def fill(self, ar, val):
        filled = False
        for i in range(0, len(ar)):
            if ar[i] == [''] and not filled:
                ar[i] = val
                filled = True
        return ar

    def oldadd_instr(self, instr1=0, instr2=0):
        block = self.cache_mem[self.cur_set][0] + 1
        tag = 3
        if block == 2:
            tag = 4
        self.cache_mem[self.cur_set][0] += 1
        if self.cache_mem[self.cur_set][0] > 1:
            self.cache_mem[self.cur_set][0] = 0
        self.cache_mem[self.cur_set][block][0] = 1
        self.cache_mem[self.cur_set][block][2] = tag
        self.cache_mem[self.cur_set][block][3] = instr1
        self.cache_mem[self.cur_set][block][4] = instr2
        self.cur_set += 1
        if self.cur_set == 4:
            self.cur_set = 0

    def oldIF(self):
        block = self.cache_mem[self.cur_read][0] + 1
        if self.cache_mem[self.cur_read][block][0] == 0:
            if self.instrholder[0] != ['']:
                temp1, self.instrholder = self.shuffle(self.instrholder)
                temp2, self.instrholder = self.shuffle(self.instrholder)
                self.add_instr(temp1, temp2)
                self.cur_read += 1
                if self.cur_read == 4:
                    self.cur_read = 0
                temp1, self.IFholder = self.shuffle(self.IFholder)
                temp2, self.IFholder = self.shuffle(self.IFholder)
                self.pre_issue = self.fill(self.pre_issue, temp1)
                self.pre_issue = self.fill(self.pre_issue, temp2)
            else:
                if self.stopping == False:
                    self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                    self.IFholder = self.fill(self.IFholder, [Disassembler.opcodeStr[self.instr],Disassembler.arg1Str[self.instr],Disassembler.arg2Str[self.instr],Disassembler.arg3Str[self.instr]])
                    self.instr += 1
                    if Disassembler.opcodeStr[self.instr - 1] == 'BREAK':
                        self.stopping = True
                if self.stopping == False:
                    self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                    self.IFholder = self.fill(self.IFholder, [Disassembler.opcodeStr[self.instr], Disassembler.arg1Str[self.instr], Disassembler.arg2Str[self.instr], Disassembler.arg3Str[self.instr]])
                    self.instr += 1
                    if Disassembler.opcodeStr[self.instr - 1] == 'BREAK':
                        self.stopping = True

    def add_instr_cache(self, s, t, data1, data2):
        self.cache_mem[int(s)][self.LRUbit[int(s)]][0] = 1
        self.cache_mem[int(s)][self.LRUbit[int(s)]][2] = t
        self.cache_mem[int(s)][self.LRUbit[int(s)]][3] = data1
        self.cache_mem[int(s)][self.LRUbit[int(s)]][4] = data2

        if self.LRUbit[int(s)] == 0:
            self.LRUbit[int(s)] = 1
        elif self.LRUbit[int(s)] == 1:
            self.LRUbit[int(s)] = 0

    def add_pre_issue(self):
        if self.pre_issue[3] == ['']:
            temp1, self.IFholder = self.shuffle(self.IFholder)
            self.pre_issue = self.fill(self.pre_issue, temp1)
        if self.pre_issue[3] == ['']:
            temp1, self.IFholder = self.shuffle(self.IFholder)
            self.pre_issue = self.fill(self.pre_issue, temp1)

    def add_new_data_cache(self, s, t, data1, data2):
        if self.cache_mem[int(s)][self.LRUbit[int(s)]][1] == 1:
            addr = self.tags_to_addr(t, s, '0')
            memindex = (int(addr) - self.dis.memStart) / 4

            if memindex+1 > len(Disassembler.mem):
                Disassembler.Disassembler.expandMem(memindex+1)
            write1 = self.dis.stringtonum(self.cache_mem[int(s)][self.LRUbit[int(s)]][3])
            write2 = self.dis.stringtonum(self.cache_mem[int(s)][self.LRUbit[int(s)]][4])
            Disassembler.mem[memindex] = self.cache_mem[int(s)][self.LRUbit[int(s)]][3]
            Disassembler.mem[memindex+1] = self.cache_mem[int(s)][self.LRUbit[int(s)]][4]

        self.cache_mem[int(s)][self.LRUbit[int(s)]][0] = 1
        self.cache_mem[int(s)][self.LRUbit[int(s)]][1] = 1
        self.cache_mem[int(s)][self.LRUbit[int(s)]][2] = t
        self.cache_mem[int(s)][self.LRUbit[int(s)]][3] = data1
        self.cache_mem[int(s)][self.LRUbit[int(s)]][4] = data2

        if self.LRUbit[int(s)] == 0:
            self.LRUbit[int(s)] = 1
        elif self.LRUbit[int(s)] == 1:
            self.LRUbit[int(s)] = 0

    def add_existing_data_cache(self, s, t, b, w, data):
        if self.cache_mem[int(s)][b][1] == 1:
            if w == 3:
                addr = self.tags_to_addr(t, s, '0')
            else:
                addr = self.tags_to_addr(t, s, '1')
            memindex = (addr-self.dis.memStart)/4
            self.dis.expandMem(memindex)
            Disassembler.mem[memindex] = self.cache_mem[int(s)][b][w]

        self.cache_mem[int(s)][b][0] = 1
        self.cache_mem[int(s)][b][1] = 1
        self.cache_mem[int(s)][b][2] = t
        self.cache_mem[int(s)][b][w] = data

        if b == 0:
            self.LRUbit[int(s)] = 1
        elif b == 1:
            self.LRUbit[int(s)] = 0

    def cache_match(self, s, t, data): #Returns Hit/Miss, Block, Word
        if self.cache_mem[int(s)][0][2] == t:
            if self.cache_mem[int(s)][0][3] == data:
                return True, 0, 3
            elif self.cache_mem[int(s)][0][4] == data:
                return True, 0, 4
            else:
                return False, 0, 0
        elif self.cache_mem[int(s)][1][2] == t:
            if self.cache_mem[int(s)][1][3] == data:
                return True, 1, 3
            elif self.cache_mem[int(s)][1][4] == data:
                return True, 1, 4
            else:
                return False, 0, 0
        else:
            return False, 0, 0

    def cache_match_addr(self, s, t):
        if self.cache_mem[int(s)][0][2] == t:
            return True, 0
        elif self.cache_mem[int(s)][1][2] == t:
            return True, 1
        else:
            return False, 0

    def tags_to_addr(self, t, s, bo):
        blockoff = bo + '00'
        s = int(s)
        t = int(t)
        setbin = bin(s)
        setbin = setbin[2:]
        tagbin = bin(t)
        tagbin = tagbin[2:]

        finalbin = '0' + tagbin + setbin + blockoff
        addr = self.dis.stringtonum(finalbin)

        return int(addr)

    def IF(self):
        if self.instrholder[1] == [''] and self.pre_issue[3] == ['']:
            pc = 96 + (self.instr * 4)
            self.holderset1, self.holdertag1 = self.getTags(pc)
            if self.stopping == False:
                in_cache, block, word = self.cache_match(int(self.holderset1), int(self.holdertag1), Disassembler.instrUnspaced[self.instr])
                if in_cache:
                    if Disassembler.opcodeStr[self.instr] == 'BREAK':
                        self.stopping = True
                    elif Disassembler.opcodeStr[self.instr] == 'J':
                        imm = Disassembler.arg1Str[self.instr]
                        imm = self.immtrim(imm)
                        immjump = int(imm) / 4
                        self.instr = immjump
                    elif Disassembler.opcodeStr[self.instr] == 'JR':
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        regval = self.registers[reg]
                        regval = int(regval) - 96
                        regjump = int(regval)/4
                        i = 0
                        while self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_alu[0][1]:
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != ['']:
                            if self.pre_mem[0][0] == 'LW' and Disassembler.arg1Str[self.instr] == self.pre_mem[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_mem[0][1]:
                            self.hazard = True
                        i = 0
                        if not self.hazard:
                            self.instr = regjump
                    elif Disassembler.opcodeStr[self.instr] == 'BNE':

                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        reg2 = Disassembler.arg2Str[self.instr]
                        reg2 = self.regtrim(reg2)
                        imm = Disassembler.arg3Str[self.instr]
                        imm = self.immtrim(imm)
                        i = 0
                        while self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1] or Disassembler.arg2Str[self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and (Disassembler.arg1Str[self.instr] == self.post_alu[0][1] or Disassembler.arg2Str[self.instr] == self.post_alu[0][1]):
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != ['']:
                            if self.pre_mem[0][0] == 'LW' and (Disassembler.arg1Str[self.instr] == self.pre_mem[i][1] or Disassembler.arg2Str[self.instr] == self.pre_mem[i][1]):
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and (Disassembler.arg1Str[self.instr] == self.post_mem[0][1] or Disassembler.arg2Str[self.instr] == self.post_mem[0][1]):
                            self.hazard = True
                        i = 0
                        if self.registers[reg] != self.registers[reg2] and not self.hazard:
                            immjump = int(imm)/4
                            self.instr = self.instr + immjump + 1
                    elif Disassembler.opcodeStr[self.instr] == 'BLEZ':
                        self.hazard = False
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        imm = Disassembler.arg2Str[self.instr]
                        imm = self.immtrim(imm)
                        i = 0
                        while self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_alu[0][1]:
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != ['']:
                            if self.pre_mem[0][0] == 'LW' and Disassembler.arg1Str[self.instr] == self.pre_mem[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_mem[0][1]:
                            self.hazard = True
                        i = 0
                        if self.registers[reg] <= 0 and not self.hazard:
                            immjump = imm / 4
                            self.instr = self.instr + immjump  + 1
                    else:
                        self.pre_issue = self.fill(self.pre_issue, [Disassembler.opcodeStr[self.instr], Disassembler.arg1Str[self.instr],
                                           Disassembler.arg2Str[self.instr], Disassembler.arg3Str[self.instr]])
                        temp1, self.IFholder = self.shuffle(self.IFholder)
                        self.instr+=1
                else:
                    if Disassembler.opcodeStr[self.instr] == 'BREAK':
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        self.stopping = True
                    elif Disassembler.opcodeStr[self.instr] == 'J':
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        imm = Disassembler.arg1Str[self.instr]
                        imm = self.immtrim(imm)
                        immjump = imm / 4
                        self.instr = immjump
                    elif Disassembler.opcodeStr[self.instr] == 'JR':
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        regval = self.registers[reg]
                        regval = int(regval) - 96
                        regjump = int(regval)/4
                        i = 0
                        while i < 2 and self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_alu[0][1]:
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != [''] and i < 2:
                            if self.pre_mem[0][0] == 'LW' and Disassembler.arg1Str[self.instr] == self.pre_mem[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_mem[0][1]:
                            self.hazard = True
                        i = 0
                        if not self.hazard:
                            self.instr = regjump
                    elif Disassembler.opcodeStr[self.instr] == 'BNE':
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        reg2 = Disassembler.arg2Str[self.instr]
                        reg2 = self.regtrim(reg2)
                        imm = Disassembler.arg3Str[self.instr]
                        imm = self.immtrim(imm)
                        i = 0
                        while i < 2 and self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1] or Disassembler.arg2Str[self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and (
                            Disassembler.arg1Str[self.instr] == self.post_alu[0][1] or Disassembler.arg2Str[
                            self.instr] == self.post_alu[0][1]):
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != [''] and i < 2:
                            if self.pre_mem[0][0] == 'LW' and (
                                Disassembler.arg1Str[self.instr] == self.pre_mem[i][1] or Disassembler.arg2Str[
                                self.instr] == self.pre_mem[i][1]):
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and (
                            Disassembler.arg1Str[self.instr] == self.post_mem[0][1] or Disassembler.arg2Str[
                            self.instr] == self.post_mem[0][1]):
                            self.hazard = True
                        i = 0
                        if self.registers[reg] != self.registers[reg2] and not self.hazard:
                            immjump = int(imm) / 4
                            self.instr = self.instr + immjump + 1
                    elif Disassembler.opcodeStr[self.instr] == 'BLEZ':
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        imm = Disassembler.arg2Str[self.instr]
                        imm = self.immtrim(imm)
                        i = 0
                        while i < 2 and self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_alu[0][1]:
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != [''] and i < 2:
                            if self.pre_mem[0][0] == 'LW' and Disassembler.arg1Str[self.instr] == self.pre_mem[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_mem[0][1]:
                            self.hazard = True
                        i = 0
                        if self.registers[reg] <= 0 and not self.hazard:
                            immjump = imm / 4
                            self.instr = self.instr + immjump + 1
                    else:
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        self.IFholder = self.fill(self.IFholder,
                                          [Disassembler.opcodeStr[self.instr], Disassembler.arg1Str[self.instr],
                                           Disassembler.arg2Str[self.instr], Disassembler.arg3Str[self.instr]])
                        self.instr += 1
            if self.stopping == False and self.instrholder[1] == [''] and self.pre_issue[3] == ['']:
                pc = 96 + (self.instr * 4)
                self.holderset2, self.holdertag2 = self.getTags(pc)
                in_cache, block, word = self.cache_match(int(self.holderset2), int(self.holdertag2), Disassembler.instrUnspaced[self.instr])
                if in_cache:
                    if Disassembler.opcodeStr[self.instr] == 'BREAK':
                        self.stopping = True
                    elif Disassembler.opcodeStr[self.instr] == 'J':
                        imm = Disassembler.arg1Str[self.instr]
                        imm = self.immtrim(imm)
                        immjump = imm / 4
                        self.instr = immjump
                    elif Disassembler.opcodeStr[self.instr] == 'JR':
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        regval = self.registers[reg]
                        regval = int(regval) - 96
                        regjump = regval/4
                        i = 0
                        while i < 2 and self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_alu[0][1]:
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != [''] and i < 2:
                            if self.pre_mem[0][0] == 'LW' and Disassembler.arg1Str[self.instr] == self.pre_mem[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_mem[0][1]:
                            self.hazard = True
                        i = 0
                        if not self.hazard:
                            self.instr = regjump
                    elif Disassembler.opcodeStr[self.instr] == 'BNE':
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        reg2 = Disassembler.arg2Str[self.instr]
                        reg2 = self.regtrim(reg2)
                        imm = Disassembler.arg3Str[self.instr]
                        imm = self.immtrim(imm)
                        i = 0
                        while i < 2 and self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1] or Disassembler.arg2Str[
                                self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and (
                            Disassembler.arg1Str[self.instr] == self.post_alu[0][1] or Disassembler.arg2Str[
                            self.instr] == self.post_alu[0][1]):
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != [''] and i < 2:
                            if self.pre_mem[0][0] == 'LW' and (
                                Disassembler.arg1Str[self.instr] == self.pre_mem[i][1] or Disassembler.arg2Str[
                                self.instr] == self.pre_mem[i][1]):
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and (
                            Disassembler.arg1Str[self.instr] == self.post_mem[0][1] or Disassembler.arg2Str[
                            self.instr] == self.post_mem[0][1]):
                            self.hazard = True
                        i = 0
                        if self.registers[reg] != self.registers[reg2] and not self.hazard:
                            immjump = int(imm) / 4
                            self.instr = self.instr + immjump + 1
                    elif Disassembler.opcodeStr[self.instr] == 'BLEZ':
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        imm = Disassembler.arg2Str[self.instr]
                        imm = self.immtrim(imm)
                        i = 0
                        while i < 2 and self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_alu[0][1]:
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != [''] and i < 2:
                            if self.pre_mem[0][0] == 'LW' and Disassembler.arg1Str[self.instr] == self.pre_mem[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_mem[0][1]:
                            self.hazard = True
                        i = 0
                        if self.registers[reg] <= 0 and not self.hazard:
                            immjump = imm / 4
                            self.instr = self.instr + immjump + 1
                    else:
                        self.pre_issue = self.fill(self.pre_issue, [Disassembler.opcodeStr[self.instr], Disassembler.arg1Str[self.instr],Disassembler.arg2Str[self.instr], Disassembler.arg3Str[self.instr]])
                        temp1, self.IFholder = self.shuffle(self.IFholder)
                        self.instr += 1
                else:
                    if Disassembler.opcodeStr[self.instr] == 'BREAK':
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        self.stopping = True
                    elif Disassembler.opcodeStr[self.instr] == 'J':
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        imm = Disassembler.arg1Str[self.instr]
                        imm = self.immtrim(imm)
                        immjump = imm / 4
                        self.instr = immjump
                    elif Disassembler.opcodeStr[self.instr] == 'JR':
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        regval = self.registers[reg]
                        regval = int(regval) - 96
                        regjump = regval / 4
                        i = 0
                        while i < 2 and self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_alu[0][1]:
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != [''] and i < 2:
                            if self.pre_mem[0][0] == 'LW' and Disassembler.arg1Str[self.instr] == self.pre_mem[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_mem[0][1]:
                            self.hazard = True
                        i = 0
                        if not self.hazard:
                            self.instr = regjump
                    elif Disassembler.opcodeStr[self.instr] == 'BNE':
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        reg2 = Disassembler.arg2Str[self.instr]
                        reg2 = self.regtrim(reg2)
                        imm = Disassembler.arg3Str[self.instr]
                        imm = self.immtrim(imm)
                        i = 0
                        while i < 2 and self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1] or Disassembler.arg2Str[
                                self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and (
                            Disassembler.arg1Str[self.instr] == self.post_alu[0][1] or Disassembler.arg2Str[
                            self.instr] == self.post_alu[0][1]):
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != [''] and i < 2:
                            if self.pre_mem[0][0] == 'LW' and (Disassembler.arg1Str[self.instr] == self.pre_mem[i][1] or Disassembler.arg2Str[self.instr] == self.pre_mem[i][1]):
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and (
                            Disassembler.arg1Str[self.instr] == self.post_mem[0][1] or Disassembler.arg2Str[
                            self.instr] == self.post_mem[0][1]):
                            self.hazard = True
                        i = 0
                        if self.registers[reg] != self.registers[reg2] and not self.hazard:
                            immjump = int(imm) / 4
                            self.instr = self.instr + immjump + 1
                    elif Disassembler.opcodeStr[self.instr] == 'BLEZ':
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        reg = Disassembler.arg1Str[self.instr]
                        reg = self.regtrim(reg)
                        imm = Disassembler.arg2Str[self.instr]
                        imm = self.immtrim(imm)
                        i = 0
                        while i < 2 and self.pre_alu[i] != ['']:
                            if Disassembler.arg1Str[self.instr] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_alu[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_alu[0][1]:
                            self.hazard = True

                        i = 0
                        while self.pre_mem[i] != [''] and i < 2:
                            if self.pre_mem[0][0] == 'LW' and Disassembler.arg1Str[self.instr] == self.pre_mem[i][1]:
                                self.hazard = True
                            i += 1
                        if self.post_mem[0] != [''] and Disassembler.arg1Str[self.instr] == self.post_mem[0][1]:
                            self.hazard = True
                        i = 0
                        if self.registers[reg] <= 0 and not self.hazard:
                            immjump = int(imm) / 4
                            self.instr = self.instr + immjump + 1
                    else:
                        self.instrholder = self.fill(self.instrholder, Disassembler.instrUnspaced[self.instr])
                        self.IFholder = self.fill(self.IFholder,
                                          [Disassembler.opcodeStr[self.instr], Disassembler.arg1Str[self.instr],
                                           Disassembler.arg2Str[self.instr], Disassembler.arg3Str[self.instr]])
                        self.instr += 1
        elif self.instrholder[0] != [''] and self.pre_issue[3] == ['']:
            if(self.instrholder[0] == '00000000000000000000000000000000'):
                temp1, self.instrholder = self.shuffle(self.instrholder)
            elif(self.instrholder[1] == '00000000000000000000000000000000'):
                temp2, self.instrholder = self.shuffle(self.instrholder)
            else:
                temp1, self.instrholder = self.shuffle(self.instrholder)
                temp2, self.instrholder = self.shuffle(self.instrholder)
                self.add_instr_cache(int(self.holderset1), int(self.holdertag1), temp1, temp2)
                self.add_pre_issue()

    def alu_hazard_check(self, j=0):
        if self.pre_issue[j][0] == 'ADDI' or self.pre_issue[j][0] == 'ADD' or self.pre_issue[j][0] == 'SUB' or \
            self.pre_issue[j][0] == 'MUL' or self.pre_issue[j][0] == 'SLL' or self.pre_issue[j][0] == 'SRL' or \
            self.pre_issue[j][0] == 'MOVZ':
            i = 0
            while self.pre_alu[i] != ['']:
                if self.pre_issue[j][2] == self.pre_alu[i][1] or self.pre_issue[j][3] == self.pre_alu[i][1]:
                    self.hazard = True
                i += 1
            if self.post_alu[0] != ['']:
                if self.pre_issue[j][2] == self.post_alu[0][1] or self.pre_issue[j][3] == self.post_alu[0][1]:
                    self.hazard = True
                    i += 1
            while self.pre_mem[i] != ['']:
                if self.pre_mem[i][0] == 'LW' and (self.pre_issue[j][2] == self.pre_mem[i][1] or self.pre_issue[j][3] == self.pre_mem[i][1]):
                    self.hazard = True
                i += 1
            if self.post_mem[0] != ['']:
                if self.pre_issue[j][2] == self.post_mem[0][1] or self.pre_issue[j][3] == self.post_mem[0][1]:
                    self.hazard = True
                    i += 1

    def mem_hazard_check(self, j=0):
        if self.pre_issue[j][0] == 'SW':
            i = 0
            while self.pre_alu[i] != ['']:
                if self.pre_issue[j][1] == self.pre_alu[i][1] or self.pre_issue[j][3] == self.pre_alu[i][1]:
                    self.hazard = True
                i += 1
            if self.post_alu[0] != ['']:
                if self.pre_issue[j][1] == self.post_alu[0][1] or self.pre_issue[j][3] == self.post_alu[0][1]:
                    self.hazard = True
                    i += 1
            while self.pre_mem[i] != ['']:
                if self.pre_mem[i][0] == 'LW' and (self.pre_issue[j][2] == self.pre_mem[i][1] or self.pre_issue[j][3] == self.pre_mem[i][1]):
                    self.hazard = True
                i += 1
            if self.post_mem[0] != ['']:
                if self.pre_issue[j][3] == self.post_mem[0][1] or self.pre_issue[j][1] == self.post_mem[0][1]:
                    self.hazard = True
                    i += 1
        elif self.pre_issue[j][0] == 'LW':
            i = 0
            while self.pre_alu[i] != ['']:
                if self.pre_issue[j][3] == self.pre_alu[i][1]:
                    self.hazard = True
                i += 1
            if self.post_alu[0] != ['']:
                if self.pre_issue[j][3] == self.post_alu[0][1]:
                    self.hazard = True
                    i += 1
            while self.pre_mem[i] != ['']:
                if self.pre_mem[i][0] == 'LW' and (self.pre_issue[j][3] == self.pre_mem[i][1]):
                    self.hazard = True
                i += 1
            if self.post_mem[0] != ['']:
                if self.pre_issue[j][3] == self.post_mem[0][1]:
                    self.hazard = True
                    i += 1


    def PreALU(self):
        for k in range(0, 2):
            if self.pre_alu[1] == [''] and not self.hazard:
                j = 0
                while j < 4 and self.issued < 2 and not self.hazard:
                    if self.pre_issue[j][0] == 'ADDI' or self.pre_issue[j][0] == 'ADD' or self.pre_issue[j][0] == 'SUB' or self.pre_issue[j][0] == 'MUL' or self.pre_issue[j][0] == 'SLL' or self.pre_issue[j][0] == 'SRL' or self.pre_issue[j][0] == 'MOVZ':
                        i = 0
                        while self.pre_alu[i] != ['']:
                            if self.pre_issue[j][2] == self.pre_alu[i][1] or self.pre_issue[j][3] == self.pre_alu[i][1]:
                                self.hazard = True
                            i += 1
                        i = 0
                        while self.pre_mem[i] != ['']:
                            if self.pre_mem[i][0] == 'LW' and (self.pre_issue[j][2] == self.pre_mem[i][1] or self.pre_issue[j][3] == self.pre_mem[i][1]):
                                self.hazard = True
                            i += 1
                        if not self.hazard:
                            temp1, self.pre_issue = self.shuffle(self.pre_issue, pos=j)
                            self.pre_alu = self.fill(self.pre_alu, temp1)
                            self.issued += 1
                        j = 4
                    j += 1

    def PostALU(self):
        if self.post_alu[0] == ['']:
            temp1, self.pre_alu = self.shuffle(self.pre_alu)
            self.post_alu = self.fill(self.post_alu, temp1)

    def PreMEM_ALU(self):
        self.issued = 0
        if self.pre_mem[1] == [''] and not self.hazard:
            if self.pre_issue[0][0] == 'SW' and self.SWI < 1:
                self.mem_hazard_check(0)
                if not self.hazard:
                    temp, self.pre_issue = self.shuffle(self.pre_issue)
                    self.pre_mem = self.fill(self.pre_mem, temp)
                    self.issued += 1
                    self.SWI = 1
            elif self.pre_issue[0][0] == 'LW' and not self.hazard:
                self.mem_hazard_check(0)
                skip = 0
                if self.pre_issue[1][0] == 'SW':
                    self.mem_hazard_check(1)
                    if self.pre_issue[1][2] == self.pre_issue[0][2] and self.pre_issue[1][3] == self.pre_issue[0][3]:
                        pass
                    else:
                        skip = 1
                        self.SWI = 1
                if not self.hazard:
                    self.issued += 1
                    temp, self.pre_issue = self.shuffle(self.pre_issue, pos=skip)
                    self.pre_mem = self.fill(self.pre_mem, temp)
        if self.pre_alu[1] == [''] and not self.hazard and self.issued < 2:
            if self.pre_issue[0][0] == 'ADDI' or self.pre_issue[0][0] == 'ADD' or self.pre_issue[0][0] == 'SUB' or self.pre_issue[0][0] == 'MUL' or self.pre_issue[0][0] == 'SLL' or self.pre_issue[0][0] == 'SRL' or self.pre_issue[0][0] == 'MOVZ':
                self.alu_hazard_check(0)
                if not self.hazard:
                    temp1, self.pre_issue = self.shuffle(self.pre_issue)
                    self.pre_alu = self.fill(self.pre_alu, temp1)
                    self.issued += 1

        if self.pre_mem[1] == [''] and not self.hazard and self.issued < 2:
            if self.pre_issue[0][0] == 'SW' and self.SWI < 1:
                self.mem_hazard_check(0)
                if not self.hazard:
                    temp, self.pre_issue = self.shuffle(self.pre_issue)
                    self.pre_mem = self.fill(self.pre_mem, temp)
                    self.issued += 1
                    self.SWI = 1
            elif self.pre_issue[0][0] == 'LW' and not self.hazard and self.issued < 2:
                self.mem_hazard_check(0)
                skip = 0
                if self.pre_issue[1][0] == 'SW':
                    self.mem_hazard_check(1)
                    if self.pre_issue[1][2] == self.pre_issue[0][2] and self.pre_issue[1][3] == self.pre_issue[0][3]:
                        pass
                    else:
                        skip = 1
                        self.SWI = 1
                if not self.hazard:
                    self.issued += 1
                    temp, self.pre_issue = self.shuffle(self.pre_issue, pos=skip)
                    self.pre_mem = self.fill(self.pre_mem, temp)
        if self.pre_alu[1] == [''] and not self.hazard:
            if self.pre_issue[0][0] == 'ADDI' or self.pre_issue[0][0] == 'ADD' or self.pre_issue[0][0] == 'SUB' or \
                self.pre_issue[0][0] == 'MUL' or self.pre_issue[0][0] == 'SLL' or self.pre_issue[0][0] == 'SRL' or \
                self.pre_issue[0][0] == 'MOVZ':
                self.alu_hazard_check(0)
                if not self.hazard:
                    temp1, self.pre_issue = self.shuffle(self.pre_issue)
                    self.pre_alu = self.fill(self.pre_alu, temp1)
                    self.issued += 1




    def PostMEM(self):
        if self.post_mem[0] == [''] and self.pre_mem[0][0] == 'SW':
            reg = self.pre_mem[0][1]
            reg = self.regtrim(reg)
            imm = self.pre_mem[0][2]
            imm = self.immtrim(imm)
            reg2 = self.pre_mem[0][3]
            reg2 = self.regtrim(reg2)

            addr = self.registers[int(reg2)] + int(imm)
            memindex = (addr - self.dis.memStart)
            memindex = memindex/4
            sets, tag = self.getTags(addr)
            if self.mem_holder == ['']:
                in_cache = False
                block = -1
                in_cache, block = self.cache_match_addr(sets, tag)
                if in_cache == True:
                    word = 0
                    if addr%8 == 0:
                        word = 3
                    else:
                        word = 4
                    self.add_existing_data_cache(sets, tag, block, word, self.registers[reg])
                    temp, self.pre_mem = self.shuffle(self.pre_mem)
                    self.SWI = 0
                else:
                    self.mem_holder = addr
            elif self.mem_holder != ['']:
                if addr%8 == 0:
                    self.dis.expandMem(memindex+1)
                    data1 = Disassembler.mem[memindex]
                    data2 = Disassembler.mem[memindex+1]
                else:
                    data1 = Disassembler.mem[memindex-1]
                    data2 = Disassembler.mem[memindex]
                self.add_new_data_cache(sets, tag, data1, data2)
                temp, self.pre_mem = self.shuffle(self.pre_mem)
                self.mem_holder = ['']
                self.SWI = 0
        elif self.post_mem[0] == [''] and self.pre_mem[0][0] == 'LW':
            reg = self.pre_mem[0][1]
            reg = self.regtrim(reg)
            imm = self.pre_mem[0][2]
            imm = self.immtrim(imm)
            reg2 = self.pre_mem[0][3]
            reg2 = self.regtrim(reg2)

            addr = self.registers[reg2] + int(imm)
            memindex = (addr - self.dis.memStart) / 4
            sets, tag = self.getTags(addr)
            if self.mem_holder == ['']:
                in_cache = False
                block = -1
                in_cache, block = self.cache_match_addr(sets, tag)
                if in_cache == True:
                    temp, self.pre_mem = self.shuffle(self.pre_mem)
                    self.post_mem = self.fill(self.post_mem, temp)
                else:
                    self.mem_holder = addr
            elif self.mem_holder != ['']:
                if addr%8 == 0:
                    data1 = Disassembler.mem[memindex]
                    data2 = Disassembler.mem[memindex+1]
                else:
                    data1 = Disassembler.mem[memindex-1]
                    data2 = Disassembler.mem[memindex]
                self.add_new_data_cache(sets, tag, data1, data2)
                temp, self.pre_mem = self.shuffle(self.pre_mem)
                self.post_mem = self.fill(self.post_mem, temp)
                self.mem_holder = ['']

    def WB(self):
        if self.post_mem[0] != ['']:
            temp1, self.post_mem = self.shuffle(self.post_mem)
            self.hazard = False
            return True, temp1
        if self.post_alu[0] != ['']:
            temp1, self.post_alu = self.shuffle(self.post_alu)
            self.hazard = False
            return True, temp1
        if self.post_alu[0] == [''] and self.post_mem[0] == ['']:
            return False, []

    def stop(self):
        self.stopping = True
        if self.pre_issue[0] == [''] and self.pre_alu[0] == [''] and self.post_alu[0] == [''] and self.pre_mem[0] == [''] and self.post_mem[0] == ['']:
            return False
        else:
            return True

    def BufferstoString(self):
        out = 'Pre-Issue Buffer:\n'
        for i in range(0, 4):
            out += '\tEntry ' + str(i) + ':'
            if self.pre_issue[i] != ['']:
                out += '\t' + '[' + self.pre_issue[i][0] + self.pre_issue[i][1] + self.pre_issue[i][2] + self.pre_issue[i][3] + ']\n'
            else:
                out += '\n'
        out += 'Pre_ALU Queue:\n'
        for i in range(0, 2):
            out += '\tEntry ' + str(i) + ':'
            if self.pre_alu[i] != ['']:
                out += '\t' + '[' + self.pre_alu[i][0] + self.pre_alu[i][1] + self.pre_alu[i][2] + self.pre_alu[i][3] + ']\n'
            else:
                out += '\n'
        out += 'Post_ALU Queue:\n'
        for i in range(0, 1):
            out += '\tEntry ' + str(i) + ':'
            if self.post_alu[i] != ['']:
                out += '\t' + '[' + self.post_alu[i][0] + self.post_alu[i][1] + self.post_alu[i][2] + self.post_alu[i][3] + ']\n'
            else:
                out += '\n'
        out += 'Pre_MEM Queue:\n'
        for i in range(0, 2):
            out += '\tEntry ' + str(i) + ':'
            if self.pre_mem[i] != ['']:
                out += '\t' + '[' + self.pre_mem[i][0] + self.pre_mem[i][1] + self.pre_mem[i][2] + self.pre_mem[i][3] + ']\n'
            else:
                out += '\n'
        out += 'Post_MEM Queue:\n'
        for i in range(0, 1):
            out += '\tEntry ' + str(i) + ':'
            if self.post_mem[i] != ['']:
                out += '\t' + '[' + self.post_mem[i][0] + self.post_mem[i][1] + self.post_mem[i][2] + self.post_mem[i][3] + ']\n'
            else:
                out += '\n'
        return out

    def CachetoString(self):
        out = 'Cache\n'
        for i in range(0, 4):
            out += 'Set ' + str(i) + ': LRU=' + str(self.LRUbit[i]) + '\n'
            for j in range(0, 2):
                out += '\tEntry ' + str(j) + ':[(' + str(self.cache_mem[i][j][0]) + ',' + str(self.cache_mem[i][j][1]) + ',' + str(self.cache_mem[i][j][2]) + ')<' + str(self.cache_mem[i][j][3]) + ',' + str(self.cache_mem[i][j][4]) + '>]\n'
        return out

    def getTags(self, num):
        tempbin = bin(num)
        tempbin = tempbin[2:]  # To get rid of the 0b at the start from bin(num)
        #Get set and tag. Add 0 to all so it is always positive (stringtonum does signed conversion)
        sbin = '0' +  tempbin[(len(tempbin) - 5):(len(tempbin) - 3)]
        s = self.stringtonum(sbin)
        tbin = '0' + tempbin[0:(len(tempbin)-5)]
        t = self.stringtonum(tbin)
        return s, t

    def regtrim(self, reg):
        reg = reg.strip("\t")
        reg = reg.strip(",")
        reg = reg.replace(" ", "")
        reg = reg.strip('(')
        reg = reg.strip(')')
        reg = reg.replace('R', '')
        return int(reg)

    def immtrim(self, imm):
        imm = imm.replace(",", '')
        imm = imm.replace('#', '')
        imm = imm.replace(' ', '')
        return imm

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

    def regtobinary(self, reg):  # Takes the register number and returns the 32 bit binary
        tempRTbin = bin(self.registers[reg])
        tempRTbin = tempRTbin[2:]  # To get rid of the 0b at the start from bin(num)

        fillstart = 32 - len(tempRTbin)
        newbin = [0] * 32
        j = 0
        for k in range(fillstart, 32, 1):
            newbin[k] = tempRTbin[j]
            j += 1

        finalbin = ''
        for k in range(0, 32):
            finalbin += str(newbin[k])

        return str(finalbin)  # Returns 32 bit binary in a 32 character string

