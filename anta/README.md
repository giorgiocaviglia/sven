ANTA 
====

tfidf computation process + similarity
--------------------------------------

1. fill media/corpus_name 

2. use appropriate filenames while uploading. Format accepted 

        ACTOR1-ACTOR2_LANGUAGE_YYYYMMDD_TITLE SPCE SEPARATED.EXT 
        
    where language is a two chars attribute, like 'EN' or 'NL', e.g:
    
        EU-USA-UK_EN_20080518_The Mysterious Island.pdf
        

3. use sync script to sync the database with the media space 
 
        ~/sven/anta/$ python sync -c corpus_name

4. use ampoule script to extract summarization 
 
        ~/sven/anta/$ python ampoule.py -c corpus_name

5. use metrics.py to manage tfidf computation (specify corpus AND language) 

        ~/sven/anta/$ python metrics.py -c corpus_name -f tfidf -l EN

6. use metrics.py to manage similarity between documents, using cosine similarity (change function ) 

        ~/sven/anta/$ python metrics.py -c corpus_name -f similarity -l EN

7. test freebase search function result per language, positional args 

     	~/sven/anta/$ python freebase.py Nirvana it

Api Documentation
-----------------

Api function are defined inside the `anta/api.py` script.
Their related urls are tastypie-like urls, that is, each url address is related to a Model Class and 
outpus vary according to the http method used to GET a single model instance, to GET a list of instances or
to DELETE or POST content.
I localhost, this is the sample url to request a specific set of Relation objects: 

     url: http://localhost/sven/anta/api/relations/?method=GET&indent&filters={%22creation_date__gt%22:%222011-10-12%2000:00%22,%22source__language%22:%22NL%22} 
		
Please note that `method` used is explicitely defined as request parameter.
Result, in json, shows the usage of filters params with the django friendly filter function by dictornary:

    {
    "status": "ok", 
    "meta": {
        "indent": true, 
        "next": {
            "limit": 50, 
            "offset": 50
        }, 
        "limit": 50, 
        "filters": {
            "creation_date__gt": "2011-10-12 00:00", 
            "source__language": "NL"
        }, 
        "offset": 0, 
        "total": 1, 
        "method": "GET"
    }, 
    "user": "admin", 
    "results": [
        {
            "polarity": "NEG", 
            "source": 56, 
            "intensity": -0.6, 
            "target": 57, 
            "owner": {
                "username": "admin", 
                "id": 2
            }, 
            "description": "basic", 
            "id": 1, 
            "creation_date": "2012-07-22T04:41:31"
        }
    ]
    }
    

Like the method, other params could be used in a GET api.
A POST request use a ModelForm to validate fields. A request like

    http://localhost/sven/anta/api/relations/?indent&method=POST

would generate an error because of the ModelForm Relation fields:

    {
    "status": "ko", 
    "userMessage": "", 
    "errorCode": "FormErrors", 
    "meta": {
        "indent": true, 
        "method": "POST", 
        "filters": []
    }, 
    "user": "admin", 
    "error": {
        "polarity": [
            "This field is required."
        ], 
        "source": [
            "This field is required."
        ], 
        "target": [
            "This field is required."
        ], 
        "description": [
            "This field is required."
        ]
    }, 
    "owner": {
        "username": "admin", 
        "id": 2
    }
    }

Delete an instance by giving the instance numeric id :

    http://localhost/sven/anta/api/relations/1/?indent&method=DELETE
    
The update function is not yet available, but basically it's a method=POST request with the ref. id.


useful sql queries 
------------------

How to get **actor / number of document per actor** 
(actor is a tag.name). Note that this does not handle overlapping
(i.e. documents are "duplicated"). 
Overlapping: get document by tag

    SELECT 
        count( DISTINCT d.id) as num_of_document, 
        t.name, 
        t.type 
    FROM `anta_document_tag` dt  
    JOIN anta_document d ON dt.document_id = d.id 
    JOIN anta_tag t ON dt.tag_id = t.id 
        WHERE t.type="actor" 
    GROUP BY name

*Note that you can filter anta_document table by `corpus_id` and `language` fields.*

Filter *document* by date
    SELECT * 
    FROM `anta_document` 
        WHERE ref_date 
            BETWEEN STR_TO_DATE('2009-03-01','%Y-%m-%d') 
            AND STR_TO_DATE('2010-01-01','%Y-%m-%d')

How to get a **cosine similarity** table between documents 

    SELECT 
        d1.id as alpha_id, d1.title as alpha_title, d1.language as alpha_language,
        d2.id as omega_id, d2.title as omega_title, d2.language as omega_language,
        y.cosine_similarity 
    FROM `anta_distance` y 
    JOIN anta_document d1 ON y.alpha_id = d1.id 
    JOIN anta_document d2 on y.omega_id = d2.id 
    ORDER BY y.`cosine_similarity`  DESC
    
Hence, get "similarity" between *actors* by their documents similarity (intermediate table)
    
    SELECT 
        d1.id as alpha_id, d1.title as alpha_title, d1.language as alpha_language,
        t1.name as alpha_actor,  
        d2.id as omega_id, d2.title as omega_title, d2.language as omega_language,
        t2.name as omega_actor,
        y.cosine_similarity 
    FROM `anta_distance` y
    JOIN anta_document_tag dt1 ON y.alpha_id = dt1.document_id
    JOIN anta_document_tag dt2 ON y.omega_id = dt2.document_id  
    JOIN anta_tag t1 ON dt1.tag_id = t1.id
    JOIN anta_tag t2 ON dt2.tag_id = t2.id
    JOIN anta_document d1 ON y.alpha_id = d1.id
    JOIN anta_document d2 on y.omega_id = d2.id
        WHERE t1.type='actor' AND t2.type='actor'
    ORDER BY t1.name, t2.name, alpha_id
    
…and finally, similarity aggregated by actors.

    SELECT 
        t1.name as alpha_actor,  
        t2.name as omega_actor,
        AVG( y.cosine_similarity ) as average_cosine_similarity
    FROM `anta_distance` y
    JOIN anta_document_tag dt1 ON y.alpha_id = dt1.document_id
    JOIN anta_document_tag dt2 ON y.omega_id = dt2.document_id  
    JOIN anta_tag t1 ON dt1.tag_id = t1.id
    JOIN anta_tag t2 ON dt2.tag_id = t2.id
    JOIN anta_document d1 ON y.alpha_id = d1.id
    JOIN anta_document d2 on y.omega_id = d2.id
         WHERE t1.type='actor' AND t2.type='actor'
    GROUP BY alpha_actor, omega_actor
    ORDER BY average_cosine_similarity

get documents where PAIRS of concept occur

	SELECT * FROM anta_document_segment ds 
	JOIN `anta_segment` s on ds.segment_id = s.id 
		WHERE stemmed LIKE '%diaspor%' OR content LIKE '%democr%' 
	ORDER BY tf DESC

get number of analysed document (raw)
	
	SELECT COUNT( DISTINCT ds.document_id ) 
	FROM  `anta_document_segment` ds
	JOIN `anta_document` d ON ds.document_id = d.id
		WHERE d.corpus_id = 1
		
get top stemmed segment per actor:
	
	SELECT 
	    t.name, MAX(ds.tfidf), AVG(tfidf), s.content, s.stemmed_refined, 
	    count( *) as distro 
	FROM `anta_document_segment` ds 
	JOIN anta_document_tag dt ON dt.document_id = ds.document_id 
	JOIN anta_tag t ON t.id = dt.tag_id 
	JOIN anta_segment s ON s.id = ds.segment_id 
	    WHERE t.type='actor' 
	GROUP BY t.id,  stemmed_refined ORDER BY `distro` DESC
	