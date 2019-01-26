import cache
import Disassembler
import sys

c = cache.CacheAndPipeline()
d = Disassembler.Disassembler(sys.argv)
addr = 188
set,block,tag = c.getTags(296)

print set + ' ' + block + ' ' + tag