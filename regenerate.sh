
        #!/bin/bash
        #set machine dir ie .
        machine_dir=$(pwd)

        echo "running codegen..."
        cd ~/ma/codegen
        ./codegen.sh $machine_dir/machine.xml machine $machine_dir

        echo "running envgen..."
        cd ~/ma/envgen
        ./envgen.sh $machine_dir/environment.xml $machine_dir

        echo "running machine.py..."
        cd ~/ma/machinic
        python3 machine.py generate --name machine --file $machine_dir/machine.yaml
    