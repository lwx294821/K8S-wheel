 #!/bin/bash
 OUTPUT=$(docker images --format="{{.Repository}}:{{.Tag}}" |xargs --no-run-if-empty -n 1)
 array=$(echo $OUTPUT | tr ' ' ' ')
 str=$(printf "%-50s" "-")
 while getopts ":t:p:" opt
 do 
   case $opt in 
     p)
     echo "${str// /-}"
     echo "Begin push images to registry [$OPTARG]"
     echo "${str// /-}"
     target_registry=$OPTARG
     for t in ${array[@]}
     do 
       echo "   > $t"
       if [[ $t =~  ^$target_registry ]]; then
        docker push $t
       else
        echo "Error tag $t :("
        exit 1
       fi 
       
     done
     echo "${str// /-}"
     echo "Finish push images :)"
     echo "${str// /-}"
     exit 0
     ;;
     t)
     echo "${str// /-}"
     echo "Begin add new tag for repository [$OPTARG]"
     echo "${str// /-}"
     for t in ${array[@]}
     do 
       echo "   > $t"
       #docker tag $t $OPTARG/$t
       #docker rmi $t
     done
     echo "${str// /-}"
     echo "Finish Refresh Tag  :)"
     echo "${str// /-}"
     exit 0
     ;;
     ?)
     echo "Unknow args $OPTARG"
     exit 1;;
   esac
 done

