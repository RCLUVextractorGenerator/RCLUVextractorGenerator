include "txl.grm"

redefine statement 
	[attr includeStatement] 
    |   [attr keysStatement] 
    |   [attr compoundsStatement] 
    |   [attr commentsStatement] 
    |   [attr tokensStatement] 
    |   [defineStatement] 
    |   [redefineStatement] 
    |   [attr ruleStatement] 
    |   [attr functionStatement] 
    |   [attr externalStatement] 
    |   [attr comment] [NL]
end redefine 

function main match [program] _ [program] end function
