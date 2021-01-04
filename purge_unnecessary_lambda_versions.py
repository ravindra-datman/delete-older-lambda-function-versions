from __future__ import absolute_import, print_function, unicode_literals
import boto3

lambda_versions_to_keep = 3
aws_profile_name = 'prod-aws' #change it according to your aws profile name (this profile must have region as well)
# Ensure that you the profile named prod-aws in ~/.aws/credentials with region, secret and access key

total_functions_processed = 0
total_code_space_saved = 0
stages_to_exclude = ["live", "prod"]

def clean_old_lambda_versions():
    global total_functions_processed
    global aws_profile_name
    global lambda_versions_to_keep
    global total_code_space_saved

    session = boto3.Session(profile_name='prod-aws')
    client = session.client('lambda')
    functions_paginator = client.get_paginator('list_functions')
    version_paginator = client.get_paginator('list_versions_by_function')
    
    for function_page in functions_paginator.paginate():
        total_functions_processed += len(function_page['Functions'])

        for function in function_page['Functions']:
            aliases = client.list_aliases(FunctionName=function['FunctionArn'])
            alias_versions = [alias['FunctionVersion'] for alias in aliases['Aliases']]
            remaining_versions_to_delete = 0
            stage = None

            tagsResponse = client.list_tags(Resource=function['FunctionArn']) #list_tags does not support versions

            if 'Tags' in tagsResponse and 'STAGE' in tagsResponse['Tags']:
                stage = tagsResponse['Tags']['STAGE']

            for version_page in version_paginator.paginate(FunctionName=function['FunctionArn']):
                remaining_versions_to_delete += (len(version_page['Versions']))
                for version in version_page['Versions']:
                    arn = version['FunctionArn']
                    code_size = version['CodeSize']
                    isAliased = bool(version['Version'] in alias_versions)

                    if version['Version'] != function['Version'] and not isAliased and remaining_versions_to_delete > lambda_versions_to_keep and stage not in stages_to_exclude:
                        print('delete_function(FunctionName={}) isAliased={} stage={}'.format(arn, isAliased, stage))
                        
                        total_code_space_saved += code_size
                        #client.delete_function(FunctionName=arn)  # uncomment me once you've checked
                    else:
                        print('keep_function(FunctionName={}) isAliased={}  stage={}'.format(arn, isAliased, stage))

                    remaining_versions_to_delete -= 1
            print("\n")
    
    print("Total functions processed: " + str(total_functions_processed))
    print("Total Code memory saved: {} GB".format(total_code_space_saved / (1024 * 1024 * 1024)))


if __name__ == '__main__':
    clean_old_lambda_versions()

