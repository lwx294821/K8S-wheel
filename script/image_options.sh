# !/bin/bash
str=$(printf "%-50s" "-")
while getopts ":r:" opt
do
  case $opt in
  r)
  echo "${str// /-}"
  echo "Image Load from  ** $OPTARG **"
  echo "${str// /-}"
  echo "REPO | VERSION| SHA256| IMAGE_FILE(tar)"
  echo "${str// /-} "
  cat $OPTARG | while read line
  do
    l=$line
    array=(${l//,/ })
    length=${#array[@]}
    if [[ $length -eq 4  ]];then
      repo=${array[0]}
      version=${array[1]}
      sha256=${array[2]}
      image_filename=${array[3]}
      echo " $length   $repo|$version| $sha256|$image_filename"   
	#docker load -i $filename
        #docker tag $sha256 $repo:$tag	
     fi
  done 
  echo "${str// /-}"
  echo "Success :)"
  ;;
  ?)
  echo "Unknow args $OPTARG"
  exit 1
  ;;
  esac
do
