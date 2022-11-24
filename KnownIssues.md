## Bugs
This section contains bugs that are known to exist but without a clear explanation. These cause the program to not run as intended/crash.

* If two users are connected to the same session in Centaurus or Sirius and one moves the importance slider for a node, it causes the other user to crash

* Certain datasets cannot be uploaded (as a custom csv) into Centaurus/Sirius. For example, the server will crash if trying to upload the `uk_health.csv` dataset. Dr. Dowling believes this has to do with the size of the dataset. Regardless, it is worth keeping note of.

## Necessary Updates
This section contains a list of parts of the system that need updating

* Node packages need updating

## Known Issues
This section contains issues within Nebula that are known to exist and the root of the problem is known. These may require quite a bit more work to fix.

* Centaurus gets varying results when searching the same term. For example, if you search *trump* as soon as you load the `uk_health.csv` dataset you will get a different result each time (different point placements, documents, attributes). 
    * This issue can be best explained in a message sent to Dr. Dowling: 
    > We recently got Centaurus up and running and everything seems to be working great with client management, server to backend communication, etc. I did notice, however, one problem. When running the old code (your master branch) in Docker we get consistent results. For example, when using the UK health dataset and searching 'trump' the points are placed in the same place each time with the same attributes and documents. However, when running the updated version of the code, this was not the case. There were varying results, meaning different point placements, documents shown, attributes shown, etc. Despite this, all of the points shown to the user were related to the searched term. This led me to suspect there were some differences in how the data was handled between Python2 and Python3. After quite a bit of detective work I believe I have finally found what is causing this issue (I'm not sure if it is considered an issue since the code is doing exactly what it is told to do). It turns out, starting in Python3.6 dictionaries keep the order in which key,value pairs are inserted. Therefore, the first seven (or whatever the limit is) documents with weight values that are inserted into certain dictionaries will be the ones that are displayed. This means that what is displayed is "random" based off of what is inserted into the dictionary first (does not mean points that are displayed are incorrect). In the old implementation of the code (using >=Python2.7), the order in which key, value pairs are inserted into the regular dictionaries was arbitrary, but consistent. This allowed the user to see the same point placements each time. I am not sure how one would go about fixing this as this is a change to how Python dictionaries work as a whole. Like I said above, what the code is doing in the updated implementation is not incorrect, as it is showing documents and attributes that pertain to the searched term. You will just not see the same points each time. Regardless, everything else seems to be working as expected. Other users can join the session, move points around, update the code, etc. Just wanted to let you know for future reference.
    * The issue is caused due to changes in Python so it may require big updates to certain files
    * As stated above, the code is not doing anything *wrong*, but the results are not the same each time. 
    * This only occurs when there is a large amount of documents matching the searched term. If you search a term with less matches, you will get consistent results. This is because the dictionary is not reaching the 'limit' on the number of documents that can match the query.
    * The location of this issue (the only place I could find it being caused; there could be more) is in `./Nebula-Pipeline/nebula/model/ImportanceModel.py`. More specifically, it is in the `_search_for_term` function (which is why it only affects Centaurus). It occurs when we are inserting key-value pairs into the `weights_delta` dictionary, located at approximately line 746.
