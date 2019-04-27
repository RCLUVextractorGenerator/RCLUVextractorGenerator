#/usr/local/bin/ruby

# Convert Makefile analysis file to csv spreadsheet
# Jim Cordy, École Polytechnique, April 2014

# Usage:    ruby 2spreadsheet.rb < DIR.makeanalysis > DIR.makeanalysis.csv

# Revised 6 Feb 2017 - fix handling of syntax errors, report failed files JRC

# Ruby assertion checks
class AssertionError < RuntimeError
end
def assert &block
    raise AssertionError unless yield
end

# Database columns
maxcols = 65000
headers = Array.new(maxcols)
values = Array.new(maxcols)

# Input expected to be formatted like so:

# === Examples/MakeEgs/Makefile.simple ===
# Makefile: Examples/MakeEgs/Makefile.simple 
# lines: 23
# continuations: 0
# comments: 1
# ...
# === Examples/MakeEgs/Makefile.vars ===
# Makefile: Examples/MakeEgs/Makefile.vars 
# lines: 42
# continuations: 2
# comments: 0
# ...

# Only output headers once
headersdone = false

# Keep track of parsing errors
parserrors = 0

# Process lines of analysis output
line = gets

while true do
    break if line == nil 
    # === Examples/MakeEgs/Makefile.vars ===
    assert {line [0..2] == "==="}

    line = gets

    # Ignore syntax error crap by resynchronizing to next file
    while ! line.match(/^[A-Za-z ].*: .*/) do
	parserrors += 1

	while true do
	    break if line == nil || line [0..2] == "===" 
	    line = gets
	end

	break if line == nil 
	line = gets
    end

    break if line == nil 

    # Makefile: Examples/MakeEgs/Makefile.simple 
    assert {line.match(/^[A-Za-z ].*: .*/)}

    # Create columns from data lines
    ncols = 0

    for i in 0..maxcols-1
	line = line.chomp

        # Makefile: Examples/MakeEgs/Makefile.simple 
        # lines: 42
	assert {line.match(/^[A-Za-z ].*: .*/)}

	colonindex = line.index(":")

	# Column header comes from data label, e.g. "lines"
	header = line [0..colonindex-1] 
	headers [i] = header

	# Column data comes from data value, e.g. "42"
	value = line [colonindex+2..-1]
	values [i] = value

	ncols += 1

	line = gets
	break if line == nil || line [0..2] == "===" 
    end 

    # Output column header row first time
    if ! headersdone then
	print headers [0] 
	for i in 1..ncols-1
	    print ",", headers [i] 
	end 
	puts ""
	headersdone = true
    end 

    # Output data row for Makefile
    print values [0]
    for i in 1..ncols-1
	print ",", values [i] 
    end 
    puts ""

end 

# Report parsing errors
STDERR.puts "#{parserrors} files failed to parse\n"

