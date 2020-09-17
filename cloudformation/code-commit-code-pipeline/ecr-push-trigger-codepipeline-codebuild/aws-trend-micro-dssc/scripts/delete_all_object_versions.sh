#!/bin/bash

bucket=$1
set -e

echo "Removing all versions from $bucket, prefix $prefix"

OIFS="$IFS" ; IFS=$'\n' ; oset="$-" ; set -f
while IFS="$OIFS" read -a line
do
    key=`echo ${line[0]} | sed 's#SPACEREPLACE# #g'` # replace the TEMPTEXT by space again (needed to temp replace because of split by all spaces by read -a above)
    versionId=${line[1]}
    echo "key: ${key} versionId: ${versionId}"
    # use doublequotes (escaped) around the key to allow for spaces in the key.
    cmd="aws s3api delete-object --bucket $bucket --key \"$key\" --version-id $versionId"
    eval $cmd
done < <(aws s3api list-object-versions --bucket $bucket --query "[Versions,DeleteMarkers][].{Key: Key, VersionId: VersionId}" --output text | sed 's# #SPACEREPLACE#g' )
