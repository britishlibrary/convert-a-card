"""Translate bib-1 error numbers to messages."""

from z3950.PyZ3950 import oids

msg_dict = {
1: 'permanent system error', # (unspecified),
2: 'temporary system error', # (unspecified),
3: 'unsupported search', # (unspecified),
4: 'Terms only exclusion (stop) words', # (unspecified),
5: 'Too many argument words', # (unspecified),
6: 'Too many boolean operators', # (unspecified),
7: 'Too many truncated words', # (unspecified),
8: 'Too many incomplete subfields', # (unspecified),
9: 'Truncated words too short', # (unspecified),
10: 'Invalid format for record number (search term)', # (unspecified),
11: 'Too many characters in search statement', # (unspecified),
12: 'Too many records retrieved', # (unspecified),
13: 'Present request out-of-range', # (unspecified),
14: 'System error in presenting records', # (unspecified),
15: 'Record not authorized to be sent intersystem', # (unspecified),
16: 'Record exceeds Preferred-message-size', # (unspecified),
17: 'Record exceeds Exceptional-record-size', # (unspecified),
18: 'Result set not supported as a search term', # (unspecified),
19: 'Only single result set as search term supported', # (unspecified),
20: 'Only ANDing of a single result set as search term', # (unspecified),
21: 'Result set exists and replace indicator off', # (unspecified),
22: 'Result set naming not supported', # (unspecified),
23: 'Specified combination of databases not supported', # (unspecified),
24: 'Element set names not supported', # (unspecified),
25: 'Specified element set name not valid for specified database', # (unspecified),
26: 'Only generic form of element set name supported', # (unspecified),
27: 'Result set no longer exists - unilaterally deleted by target', # (unspecified),
28: 'Result set is in use', # (unspecified),
29: 'One of the specified databases is locked', # (unspecified),
30: 'Specified result set does not exist', # (unspecified),
31: 'Resources exhausted - no results available', # (unspecified),
32: 'Resources exhausted - unpredictable partial results available', # (unspecified),
33: 'Resources exhausted - valid subset of results available', # (unspecified),
100: '(unspecified) error', # (unspecified),
101: 'Access-control failure', # (unspecified),
102: 'Challenge required, could not be issued - operation terminated', # (unspecified),
103: 'Challenge required, could not be issued - record not included', # (unspecified),
104: 'Challenge failed - record not included', # (unspecified),
105: 'Terminated at origin request', # (unspecified),
106: 'No abstract syntaxes agreed to for this record', # (unspecified),
107: 'Query type not supported', # (unspecified),
108: 'Malformed query', # (unspecified),
109: 'Database unavailable', # database name,
110: 'Operator unsupported', # operator,
111: 'Too many databases specified', # maximum,
112: 'Too many result sets created', # maximum,
113: 'Unsupported attribute type', # type,
114: 'Unsupported Use attribute', # value,
115: 'Unsupported term value for Use attribute', # term,
116: 'Use attribute required but not supplied', # (unspecified),
117: 'Unsupported Relation attribute', # value,
118: 'Unsupported Structure attribute', # value,
119: 'Unsupported Position attribute', # value,
120: 'Unsupported Truncation attribute', # value,
121: 'Unsupported Attribute Set', # oid,
122: 'Unsupported Completeness attribute', # value,
123: 'Unsupported attribute combination', # (unspecified),
124: 'Unsupported coded value for term', # value,
125: 'Malformed search term', # (unspecified),
126: 'Illegal term value for attribute', # term,
127: 'Unparsable format for un-normalized value', # value,
128: 'Illegal result set name', # name,
129: 'Proximity search of sets not supported', # (unspecified),
130: 'Illegal result set in proximity search', # result set name,
131: 'Unsupported proximity relation', # value,
132: 'Unsupported proximity unit code', # value,
201: 'Proximity not supported with this attribute combination attribute', # list,
202: 'Unsupported distance for proximity', # distance,
203: 'Ordered flag not supported for proximity', # (unspecified),
205: 'Only zero step size supported for Scan', # (unspecified),
206: 'Specified step size not supported for Scan step', # size,
207: 'Cannot sort according to sequence', # sequence,
208: 'No result set name supplied on Sort', # (unspecified),
209: 'Generic sort not supported (database-specific sort only supported)', # (unspecified),
210: 'Database specific sort not supported', # (unspecified),
211: 'Too many sort keys', # number,
212: 'Duplicate sort keys', # key,
213: 'Unsupported missing data action', # value,
214: 'Illegal sort relation', # relation,
215: 'Illegal case value', # value,
216: 'Illegal missing data action', # value,
217: 'Segmentation: Cannot guarantee records will fit in specified segments', # (unspecified),
218: 'ES: Package name already in use', # name,
219: 'ES: no such package, on modify/delete', # name,
220: 'ES: quota exceeded', # (unspecified),
221: 'ES: extended service type not supported', # type,
222: 'ES: permission denied on ES - id not authorized', # (unspecified),
223: 'ES: permission denied on ES - cannot modify or delete', # (unspecified),
224: 'ES: immediate execution failed', # (unspecified),
225: 'ES: immediate execution not supported for this service', # (unspecified),
226: 'ES: immediate execution not supported for these parameters', # (unspecified),
227: 'No data available in requested record syntax', # (unspecified),
228: 'Scan: malformed scan', # (unspecified),
229: 'Term type not supported', # type,
230: 'Sort: too many input results', # max,
231: 'Sort: incompatible record formats', # (unspecified),
232: 'Scan: term list not supported', # alternative term list,
233: 'Scan: unsupported value of position-in-response', # value,
234: 'Too many index terms processed', # number of terms,
235: 'Database does not exist', # database name,
236: 'Access to specified database denied', # database name,
237: 'Sort: illegal sort', # (unspecified),
238: 'Record not available in requested syntax', # alternative suggested syntax(es),
239: 'Record syntax not supported', # syntax,
240: 'Scan: Resources exhausted looking for satisfying terms', # (unspecified),
241: 'Scan: Beginning or end of term list', # (unspecified),
242: 'Segmentation: max-segment-size too small to segment record', # smallest acceptable size,
243: 'Present: additional-ranges parameter not supported', # (unspecified),
244: 'Present: comp-spec parameter not supported', # (unspecified),
245: "Type-1 query: restriction ('resultAttr') operand not supported:", # (unspecified),
246: "Type-1 query: 'complex' attributeValue not supported", # (unspecified),
247: "Type-1 query: 'attributeSet' as part of AttributeElement not supported", # (unspecified),
1001: 'Malformed APDU',
1002: 'ES: EXTERNAL form of Item Order request not supported.', #  ,
1003: 'ES: Result set item form of Item Order request not supported.', #  ,
1004: 'ES: Extended services not supported unless access control is in effect.', #  ,
1005: 'Response records in Search response not supported.', #  ,
1006: 'Response records in Search response not possible for specified database (or database combination). See note 1.', #  ,
1007: 'No Explain server. See note 2.', # pointers to servers that have a surrogate Explain database for this server.,
1008: 'ES: missing mandatory parameter for specified function', # parameter,
1009: 'ES: Item Order, unsupported OID in itemRequest.', # OID,
1010: 'Init/AC: Bad Userid', #  ,
1011: 'Init/AC: Bad Userid and/or Password', #  ,
1012: 'Init/AC: No searches remaining (pre-purchased searches exhausted)', #  ,
1013: 'Init/AC: Incorrect interface type (specified id valid only when used with a particular access method or client)', #  ,
1014: 'Init/AC: Authentication System error', #  ,
1015: 'Init/AC: Maximum number of simultaneous sessions for Userid', #  ,
1016: 'Init/AC: Blocked network address', #  ,
1017: 'Init/AC: No databases available for specified userId', #  ,
1018: 'Init/AC: System temporarily out of resources', #  ,
1019: 'Init/AC: System not available due to maintenance', # when it's expected back up,
1020: 'Init/AC: System temporarily unavailable', # when it's expected back up,
1021: 'Init/AC: Account has expired', #  ,
1022: 'Init/AC: Password has expired so a new one must be supplied', #  ,
1023: 'Init/AC: Password has been changed by an administrator so a new one must be supplied', #  ,
1024: 'Unsupported Attribute. See note 3.', # an unstructured string indicating the object identifier of the attribute set id, the numeric value of the attribute type, and the numeric value of the attribute.,
1025: 'Service not supported for this database', #  ,
1026: 'Record cannot be opened because it is locked', #  ,
1027: 'SQL error', #  ,
1028: 'Record deleted', #  ,
1029: 'Scan: too many terms requested.', # Addinfo: max terms supported,
1040: 'ES: Invalid function', # function,
1041: 'ES: Error in retention time', # (unspecified),
1042: 'ES: Permissions data not understood', # permissions,
1043: 'ES: Invalid OID for task specific parameters', # oid,
1044: 'ES: Invalid action', # action,
1045: 'ES: Unknown schema', # schema,
1046: 'ES: Too many records in package', # maximum number allowed,
1047: 'ES: Invalid wait action', # wait action,
1048: 'ES: Cannot create task package -- exceeds maximum permissable size (see note 4)', # maximum task package size,
1049: 'ES: Cannot return task package -- exceeds maximum permissable size for ES response (see note 5)', # maximum task package size for ES response,
1050: 'ES: Extended services request too large (see note 6)', # maximum size of extended services request,
1051: 'Scan: Attribute set id required -- not supplied', #  ,
1052: 'ES: Cannot process task package record -- exceeds maximum permissible record size for ES (see note 7)', # maximum record size for ES,
1053: 'ES: Cannot return task package record -- exceeds maximum permissible record size for ES response (see note 8)', # maximum record size for ES response,
1054: 'Init: Required negotiation record not included', # oid(s) of required negotiation record(s),
1055: 'Init: negotiation option required', #  ,
1056: 'Attribute not supported for database', # attribute (oid, type, and value), and database name,
1057: 'ES: Unsupported value of task package parameter (See Note 9)', # parameter and value,
1058: 'Duplicate Detection: Cannot dedup on requested record portion', #  ,
1059: 'Duplicate Detection: Requested detection criterion not supported', # detection criterion,
1060: 'Duplicate Detection: Requested level of match not supported', #  ,
1061: 'Duplicate Detection: Requested regular expression not supported', #  ,
1062: 'Duplicate Detection: Cannot do clustering', #  ,
1063: 'Duplicate Detection: Retention criterion not supported', # retention criterion,
1064: 'Duplicate Detection: Requested number (or percentage) of entries for retention too large', #  ,
1065: 'Duplicate Detection: Requested sort criterion not supported', # sort criterion,
1066: 'CompSpec: Unknown schema, or schema not supported.', #  ,
1067: 'Encapsulation: Encapsulated sequence of PDUs not supported.', # specific unsupported sequence,
1068: 'Encapsulation: Base operation (and encapsulated PDUs) not executed based on pre-screening analysis.', #  ,
1069: 'No syntaxes available for this request. See note 10.', #  ,
1070: 'user not authorized to receive record(s) in requested syntax', #  ,
1071: 'preferredRecordSyntax not supplied', #  ,
1072: 'Query term includes characters that do not translate into the target character set.', # Characters that do not translate
}


def lookup_errmsg (condition, oid):
    if oid != oids.Z3950_DIAG_BIB1_ov:
        return "Unknown oid: %s condition %d" % (str (oid), condition)
    if condition in msg_dict:
        return msg_dict[condition]
    else:
        return "Unknown BIB-1 error condition %d" % (condition,)