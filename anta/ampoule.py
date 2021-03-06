import os,sys,mimetypes
from datetime import datetime
# from warnings import filterwarnings
# import MySQLdb as Database

# filterwarnings('ignore', category = Database.Warning)

# get path of the django project
path = ("/").join( sys.path[0].split("/")[:-2] )

if path not in sys.path:
    sys.path.append(path)
    
os.environ['DJANGO_SETTINGS_MODULE'] = 'sven.settings'
from django.conf import settings
from django.db.models import Count
from optparse import OptionParser
from sven.anta.models import *
from sven.anta.sync import error, sync
from sven.anta.log import log
from sven.anta.distiller import distill, log_routine
from sven.anta.utils import *
from pattern.metrics import levenshtein, similarity, DICE
from sven.anta.freebase import search as fsearch
#
#    =================
#    ---- ampoule ----
#    =================
# 

def dbpedia():
	print "dbpedia"

def freebase( options, parser ):
	# needs to have an api key provided
	# options['api_key']
	# @todo handle transaction 
	try:
		corpus = Corpus.objects.get( name=options.corpus )
	except:
		return error( message="corpus was not found! use sync.py script to load corpora", parser=parser )
	
	# for each segments in given documents
	# 
	segments = Segment.objects.filter( documents__corpus = corpus).annotate(num_concepts=Count('concepts'))
	num_of_segments = segments.count()
	
	
	print "[info] freebase analysis"
	print "[info] freebase api key:", options.freebasekey
	print "[info] num of segments:", num_of_segments
	
	
	for s in segments:
		
		
		# quick and dirty test
		
		
		
		#if s.num_concepts > 2:
			
		#	print s.concepts
		#try:
		print "[info] search:",s.content, s.language, s.num_concepts
		results =  fsearch({'query':s.content, 'key':options.freebasekey, 'lang':s.language.lower()}, stop_universes=[
			"/book/written_work", 
			"book/book/",
			"/film/film", "/music/track",
			"/book/book_edition",
			"/tv/tv_series_episode",
			"/fictional_universe/work_of_fiction",
			"/music/composition",
			"/music/release",
			"/tv/tv_program"
		])
		for r in results:
			
			# get existing relata
			try:
				relatum = Relatum.objects.get( slug=r['notable']['id'], language=s.language )
			except:
				relatum = Relatum( 
					content		= r['name'],
					language	= s.language,
					slug		= r['notable']['id'],
					name		= r['notable']['name']
				)
				relatum.save()
			
			# skip if relationship between relatum and segment exists
			relation = Segment_Semantic_Relation( segment=s, relatum=relatum )
			try:
				relation.save()
			except:
				continue
		
		#print "[failed]",s.content, s.language, s.num_concepts
		
#
# Find and store duplicate candidates
#
def duplicates( options, parser ):
	# get corpus, else exit
	try:
		corpus = Corpus.objects.get( name=options.corpus )
	except:
		return error( message="corpus was not found! use sync.py script to load corpora", parser=parser )
	
	#  number of segments inside the corpus
	document_segments = Document_Segment.objects.filter(document__corpus = corpus)
	num_of_segments = document_segments.count()
	# print similarity("ciao", "caio", metric=DICE)
	
	c = 0
	for i in range(0, num_of_segments ):
		for j in range (i+1, num_of_segments ):
			#print i,j, document_segments[i].segment.stemmed, document_segments[j].segment.stemmed
			a = document_segments[i].segment.stemmed
			b = document_segments[j].segment.stemmed
			
			if a == b:
				# equal strings? not now, please
				c+=1
				continue
				
			dl = len(a) - len(b)
			ml = max( len(a), len(b) )
			
			if abs(dl) > ml/10.0:
				continue
			
			
			
			# test levensh
			ratio = 1-levenshtein(a,b)/float(ml)
			
			if ratio < .75:
				continue
			# print similarity(a, b, metric=DICE)
			print
			print ratio
			print " ", document_segments[i].segment.stemmed, document_segments[j].segment.stemmed
			print " ", document_segments[i].segment.content, document_segments[j].segment.content
			print
			
			c+=1
		# inner cycle
		
		#break
	print "found", c, "duplicates"
	
	#print levenshtein("aituo", "atuio")

#
# perform a regular expression to correct segment
# @todo
#
def executere(options, parser ):
	try:
		corpus = Corpus.objects.get( name=options.corpus )
	except:
		return error( message="corpus was not found! use sync.py script to load corpora", parser=parser )
	
def basic( options, parser ):
	print "[info] basic function, simple tf computation"
	options.noautoformat = False
	sync( options, parser )
	decant( options, parser )

# decant function,
# foreach documents
#    extract with distill tags and NP
#       attach tags to document (automatic pseudotagging)
#    save every NP found along with specifid tf (term frequency )
# once finished
#    recalculate tf/idf foreach tf
#
def decant( corpus, routine, ref_completion=1.0 ):
	# path = settings.MEDIA_ROOT + options.corpus
	# print NL_STOPWORDS
	
	# get document corpus
	print "[info] starting pattern analysis on corpus:",corpus.id, corpus.name
	
	log_routine( routine, entry="[info] starting pattern analysis on corpus: %s %s" % corpus.id % corpus.name )
	
	raise Exception("stop here")

	log_routine(routine, entry="after exception raised")
	return

	# create or resume analysis
	try: 
		analysis = Analysis.objects.get(corpus=corpus, type="PT")

		print "[info] analysis:", analysis.id, "found, current document:",analysis.document
		
		if analysis.status == "ERR":
			print "[info] analysis blocked:", analysis.id, "with ERR status, force restart.."
		
		elif analysis.status != "OK":
			print "[warning] analysis:", analysis.id, "not completed, status:", analysis.status
			print "[info] restart analysis."
			
	except Analysis.DoesNotExist:
		analysis = Analysis( corpus=corpus, type="PT", start_date=datetime.utcnow(), status="CRE" )
		analysis.save()	
		print "[info] analysis created:", analysis.id, "at",analysis.start_date

	print "[info] analysis status:",  analysis.id, "at", analysis.status

	if analysis.document is None:
		documents = Document.objects.filter(corpus__id=corpus.id)
		print "[info] analysis documentis None, then start from first available document"
	else:
		documents = Document.objects.filter(corpus__id=corpus.id, id__gt=analysis.document.id)
		if documents.count() == 0:
			documents = Document.objects.filter(corpus__id=corpus.id)

	# pending status for current analysis
	analysis.status = "PN"
	analysis.save()
	
	for d in documents:
		print
		print " document ",d.id
		print " ---------------------------------------"
		print
		

		# a = Analysis( document=d, )
		print "[info] document mimetype:",d.mime_type

		textified =  textify( d, settings.MEDIA_ROOT )
		
		if textified == False:
			print "[error] while textify file ",d.id, d.title
			analysis.status="ERR"
			analysis.save()
			exit
		
		textified = textified.replace("%20"," ")
		
		# update analysis with current valid document
		analysis.document = d
		analysis.save()
		
		
		# load storpwords for document d language
		if d.language == "NL": 
			stopwords = NL_STOPWORDS
		else:
			stopwords = EN_STOPWORDS
		
		print "[info] document language:",d.language
		print "[info] analysis started on doc ", d.id,"'", d.title,"'", d.language.lower(), "file:",textified
		
		#start distill anaysis, exclude given stopwors
		distilled = distill( filename=textified, language=d.language.lower(), stopwords=stopwords )
		
		# append keywords as tag for the document
		for k in distilled['keywords']:
			# print k
			candidate = k[1]
			# get tag
			try:
				t = Tag.objects.get( name=candidate, type="keyword" )
			except:
				# todo lemma version of a word according to language
				t = Tag( name=candidate, type="keyword" )
				try:
					t.save()
				except:
					print "[warning] unable to save as tag:", candidate
					continue
		 	
		 	# set tag documnt relation
		 	try:
		 		td = Document_Tag( document=d, tag=t)	
		 		td.save()
		 	except:
		 		#relation exist,
		 		continue
		
		# segment
		first = True
		for segment in distilled['segments']:
						

			if len(segment[0]) > 128:
				print "[warning] sample 'segment' will be truncated:", segment[0]
				continue
			try:
				s = Segment.objects.get( content=segment[0][:128], language=d.language)
			except:
				s = Segment( content=segment[0][:128], stemmed=re.sub("\s+", ' ', " ".join(segment[1])[:128] ), language=d.language )
				try:
					s.save()
				except:
					print "[warning] unable to save segment:", segment[0][:128]
					continue
			try:
				sd = Document_Segment.objects.get( document=d, segment=s )
			except:
				sd = Document_Segment( document=d, segment=s, tf=segment[2] )
				sd.save()
				# relationship exist
			if first:
				print "[info] sample 'segment' saved:", s.id, s.content, ", stem:", s.stemmed ,", tf:", sd.tf
				
			
			# save concept and attach
			for k in segment[1]:
				# ignore numbers				
				k = re.sub("[\d\-\.]+","", k)
				if len(k) < 2:
					continue
				try:
					c = Concept.objects.get( content=k, language=d.language)
				except:
					try:
						c = Concept( content=k, language=d.language )

						c.save()
					except:
						print "[warning] unable to save concept: ", k
						continue
				try:
					sc = Segment_Concept.objects.get( segment=s, concept=c )
				except:
					sc = Segment_Concept( segment=s, concept=c )
					sc.save()	
					
				if first:
					print "[info] sample 'concept' saved:",c.id, c.content

			first = False
			
		
		
		print "[info] analysis ended on doc", d.id,"'", d.title,"'"
	
	print "[info] analysis completed on corpus:", corpus.id
	analysis.status = "OK"
	analysis.end_date = datetime.utcnow()
	analysis.save()
		
		
def main( argv):
	usage = "usage: %prog -c corpus_name [-f]"
	parser = OptionParser( usage=usage )
	parser.add_option(
		"-c", "--corpus", dest="corpus",
		help="an anta corpus_name")
	
	parser.add_option(
		"-f", "--function", dest="function", default="decant", 
		help="function to be performed. Default to 'ampoule', to computate tf")
	
	parser.add_option(
		"-k", "--freebasekey", dest="freebasekey", default="",
		help="freebase api key (use with function 'freebase'")
	
	
	( options, argv ) = parser.parse_args()
	
	if options.corpus is None:
		error( message="Use -c to specify the corpus", parser=parser )
	
	if options.function is "decant":
		return decant(options.corpus, parser )
	elif options.function == "duplicates":
		return duplicates(options, parser )
	elif options.function == "freebase":
		return freebase( options, parser )
	else :
		return basic(options, parser)	
	
	error( message="function '"+options.function+"'was not found!", parser=parser )
	
	
	
if __name__ == '__main__':
	# get corpus name
	main(sys.argv[1:])
