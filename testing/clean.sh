# This for comparing text files
# TO CHANGE TYPE edit the two files below 
    file_to_delete="output.txt"
    comparison_file="input.txt"

    server_log = "server_errors.txt"
    client_log = "client_errors.txt"
    # Check if the file to delete exists
    if [ -f "$file_to_delete" ]; then
        cmp "$comparison_file" "$file_to_delete"
        if [ $? -eq 0 ]; then
          echo "Files are equal"
        else
            echo "Files aren't equal."
        fi
        rm "$file_to_delete"
        rm "$client_log"
        rm "$server_log"
    else
        echo "$file_to_delete was not created by the Python program."
        rm "$client_log"
        rm "$server_log"
    fi
