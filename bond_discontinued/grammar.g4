grammar bond;

assignment: VAR '=' expression;
expression: term;
term: factor ('+' | '-') factor;
factor: exponent ('*' | '/' | '%') exponent;
exponent: unary '^' exponent;
unary: (('-' | '+' | '!') unary) | primary;
primary: STRING | INTEGER | fn_call | grouping | VAR;
grouping: '(' expression ')';
fn_call: IDENTIFIER '(' (expression ',')* expression? ')';

SPACE: (' ' | '\n' | '\r' | '\t' | '\v') {$channel = HIDDEN;};
COMMENT: '#' (~('\r' | '\n'))* {$channel = HIDDEN;};

VAR: '$-' VAR_INNER '-$';
VAR_INNER:
	VAR_CHAR_NOSPACE VAR_CHAR* VAR_CHAR_NOSPACE
	| VAR_CHAR_NOSPACE;
VAR_CHAR: [a-zA-Z0-9_] | '-' | ' ';
VAR_CHAR_NOSPACE: [a-zA-Z0-9_] | '-';

STRING: '"' STRING_CHAR* '"';
STRING_CHAR: ESCAPE_CODE | ANY_UTF8;
ESCAPE_CODE:
	'\\' (
		'a'
		| 'b'
		| 'f'
		| 'n'
		| 'r'
		| 't'
		| 'v'
		| ('x' HEX_DIG HEX_DIG)
		| ('u' HEX_DIG HEX_DIG HEX_DIG HEX_DIG)
		| (
			'U' HEX_DIG HEX_DIG HEX_DIG HEX_DIG HEX_DIG HEX_DIG HEX_DIG HEX_DIG
		)
		| ANY_UTF8
	);
ANY_UTF8: [\U00000000-\U0010FFFF];
HEX_DIG: [0-9a-fA-F];

INTEGER: [0-9]+;

IDENTIFIER: [a-zA-Z_] [a-zA-Z0-9_]*;