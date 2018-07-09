#######################################################################################
###                                  preprocess.py                                  ###
#######################################################################################
# https://github.com/unimelbbionlp/BioNLPST2016/blob/master/preprocess.py

import sys
import re
import nltk
from nltk.tokenize import sent_tokenize
from corenlp import coreNLP
from corenlp import clsEntity


########################################      main function     ############################################
def generate_data_points(documentId, outdir):
	'''
	Generate data points and print it out, one per line
	'''
	nlpObj = coreNLP()
	nlpObj.parse(documentId + ".txt.out")
	
	a1file = documentId + ".a1"
	listOfEntities= get_entitylist_from_a1file(a1file , nlpObj)

	a2file = documentId + ".a2" 
	all_relations = get_all_relations(a2file)

	for ptr1 in range(len(listOfEntities)):
		for ptr2 in range(len(listOfEntities)):
			# no reflexive, relations ie. relations of type (a,a)
			if ptr2 == ptr1:
				continue 

			e1 = listOfEntities[ptr1]
			e2 = listOfEntities[ptr2]

			# just a heuristic to speed up -- skip entity pairs that are too far apart
			if abs(e1.sentenceId - e2.sentenceId) > 8 :
				continue 

			relation_name = all_relations.get((e1.entityId,e2.entityId),  "NOT_RELATED")  # get_relation_label(e1, e2, a2filedata)

			print("EntityArg1:", e1.get_display(), "\t", 
				  "EntityArg2:", e2.get_display(), "\t", 
				  "RelationLabel:", relation_name, "\t",
				  "Sentence_Numbers:", e1.sentenceId, e2.sentenceId, "\t",
				  "Bag_Of_Words:", get_feature_bow(e1, e2, nlpObj), "\t",
				  "Parse_Tree:", get_feature_parsetree(e1, e2, nlpObj))


#########################     parse input files     ############################
### entity
def get_entitylist_from_a1file(a1file, nlpObj):			
	listOfEntities = []
	for line in open(a1file).readlines():
		entityId = line.split("\t")[0].strip()
		entityDesc = line.split("\t")[2].strip()
		try:
			tarr = line.split("\t")[1].replace(";", " ").split()
			entityType, start, end = tarr[0], tarr[1], tarr[2] # line.split("\t")[1].split(" ")
			start = int(start)
			end = int(end)
			sentenceId = nlpObj.getSentenceId(start,end)
		except Exception as e:
			print("BROKEN ANNOTATION NOT HANDLED", line , tarr, file=sys.stderr)
			print("from file: ", a1file, file=sys.stderr)
			print("exception: ", str(e), file=sys.stderr)
			sys.exit(-1)
			continue

		if sentenceId == -1 : # if it is still -1, give up
			print("Giving up,", 
				  "invalid entity ?.." , documentId, sentenceId, entityType, entityDesc, start, end, 
				  "did not find ", re.sub(r"[\s\n]+", "_", entityDesc, re.DOTALL) , " in ", nlpObj.rawText, file=sys.stderr)
			sys.exit(-1)

		listOfEntities.append(clsEntity(entityId, entityDesc, entityType, start, end, sentenceId, documentId))

	return listOfEntities

### relation
def get_all_relations(a2file):
	relations = {}
	try :
		for line in open(a2file).readlines():
			relid, relname, entity1, entity2 = line.split()
			role1, e1 = entity1.split(":")
			role2, e2 = entity2.split(":")
			relations[(e1,e2)] = relname
	except:
		print("No a2file ", a2file , "empty relations", file=sys.stderr)

	return relations


######################################    add feature definitions here   ##################################
### bag of words
def get_feature_bow(e1, e2, nlpObj):
	s1 = e1.sentenceId # nlpObj.getSentenceId(e1.start, e1.end) 
	s2 = e2.sentenceId # nlpObj.getSentenceId(e2.start, e2.end) 

	if s1 != s2: 
		# print("entity pair is outside a sentence boundary")
		retval = nlpObj.rawText[s1] + " SENTENCE_BOUNDARY " + nlpObj.rawText[s2]
	else:
		retval = nlpObj.rawText[s1]	

	return re.sub(r"[^\w]+", " ", retval) #anything other than alpha-numerals

### parse tree
def get_feature_parsetree(e1, e2, nlpObj):
	# find the sentence corresponding to e1 e2
	s1 = e1.sentenceId # nlpObj.getSentenceId(e1.start, e1.end) 
	s2 = e2.sentenceId # nlpObj.getSentenceId(e2.start, e2.end) 
	if s1 != s2 : 
		# print("entity pair is outside a sentence boundary")
		pt1 = re.sub(r"[\n\s]+"," ", nlpObj.parseTree[s1])
		pt2 = re.sub(r"[\n\s]+"," ", nlpObj.parseTree[s2])
		retval = pt1 + " SENTENCE_BOUNDARY " + pt2
	else:
		retval = nlpObj.parseTree[s1] 

	return re.sub(r"[\s\n]+", " ", retval) # white space squeeze

############################################################		
def get_relation_label(entity1, entity2, a2filedata ):
	m = re.match(r".*\s+(.*)\s(\w+):" + entity1.entityId + r"\s(\w+):" + entity2.entityId + r"[^\d]", a2filedata, re.DOTALL) 
	if m :
		relation_label = m.group(1)
		return relation_label
	else:
		return "NOT_RELATED"

def get_candidate_pairs(listOfEntities, relation_types):
	e1_lst = []
	e2_lst = []
	for e in listOfEntities :
		if "Binds_To" in relation_types :
			if e.entityType in ["RNA","Protein","Protein_Family", "Protein_Complex", "Protein_Domain", "Hormone"] :
				e1_lst.append( e )
			if e.entityType in ["Gene","Gene_Family" ,"Box", "Promoter", "RNA", "Protein", "Protein_Family", "Protein_Complex", "Protein_Domain","Hormone"] :
				e2_lst.append( e )

	retlst = []
	for e1 in e1_lst :
		for e2 in e2_lst :
			if e1.entityId != e2.entityId : #  no self relations possible like t1-t1..
				retlst.append( (e1,e2) )
	return retlst 



if __name__ == "__main__":
	# produce_data_points(documentId) # docmentId is SeeDev-binary-10662856-1.txt  # pmid-passageid
	documentId = sys.argv[1]
	generate_data_points(documentId, outdir=sys.argv[2]) # docmentId is SeeDev-binary-10662856-1.txt  #pmid-passageid
