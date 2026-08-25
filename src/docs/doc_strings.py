card_table_instructions = """
    Select a card using the column next to ID. Cards already matched are highlighted green.
    Cards where a user has decided no matches are appropriate are highlighted orange.
    Sort by `Selected OCLC #` to show only unmatched cards, and avoid having to scroll as far after matching a card.
"""

oclc_num_warning = """
The recorded OCLC number of the selected match and its actual OCLC number do not match.
Contact harry.lloyd@bl.uk to debug
"""

min_cat_help_text = """
Minimal cataloguing view shows only:  
100 - Author  
245 - Title  
260 - Publication info  
300s - Physical description  
600s - Subject Access  
880s - Original script representation

In full cataloguing view the following are excluded:  
063 - NLM classification number [Obsolete]  
064 - [Obsolete]  
068 - [Obsolete]  
072 - Subject category code  
078 - [Obsolete]  
079 - [Obsolete]  
250 - Edition statement  
776 - Additional physical forms  

These were agreed with the Chinese cataloguing/curatorial team but can be changed. 
"""

max_to_display_help = """
Select the number of records to display in the MARC table above.  
Setting this value very high can lead to lots of mostly blank rows to scroll through.
"""

date_select_help = """
Records with no publication date will remain included in the MARC table. 
All records including records with no publication date are included by default
when the sliders are in their default end positions. 
Publication year defined as a 4-digit number in 260$c
"""

generic_field_search_help = """
For multiple fields separate terms by a semi-colon. 
e.g. if specifying fields 010, 300 then search term might be '2001627090; 140 pages'.
Searching on a field with repeat fields searches all the repeat fields
"""

sort_options_help = """
The default is the order in which results are returned from Worldcat.
If more than one option is selected results will be sorted sequentially in the order options have been selected.
"""

derivation_complete = """
Click 'Derivation complete' if you have finished deriving the record for this card in Record Manager. 
This will mark it complete in the card table.
"""