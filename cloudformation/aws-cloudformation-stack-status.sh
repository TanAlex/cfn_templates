#!/bin/bash
#
# aws-cloudformation-stack-status --region $region --watch --stack-name $stack
#
# See: https://github.com/alestic/aws-cloudformation-stack-status
#
region_opt=
color_opt=
profile_opt=
stack_names=
watch=
red_font=
red_background=
green_font=
yellow_font=
underline=
no_underline=
no_decoration=

function decorate_text() {
  red_font='\e[0;31m'
  red_background='\e[41m'
  green_font='\e[0;32m'
  yellow_font='\e[0;33m'
  underline='\e[4m'
  no_underline='\e[24m'
  no_decoration='\e[0m'
}
while [ $# -gt 0 ]; do
  case $1 in
    --region)     region_opt="--region $2";               shift 2 ;;
    --profile)    profile_opt="--profile $2";             shift 2 ;;
    --stack-name) stack_names="$stack_names $2";          shift 2 ;;
    --watch)      watch=1;                                shift ;;
    --color)      decorate_text;color_opt="--color";      shift ;;
    --*)          echo "$0: Unrecognized option: $1" >&2; exit 1  ;;
    *) break ;;
  esac
done
set -- $stack_names $@

if [ -n "$watch" ]; then
  exec watch $color_opt -t -n1 $0 $color_opt $region_opt $profile_opt "$@"
fi

for stack_name; do
  aws cloudformation describe-stack-events \
    $region_opt \
    $profile_opt \
    --stack-name "$stack_name" \
    --output text \
    --query 'StackEvents[*].[ResourceStatus,LogicalResourceId,ResourceType,Timestamp]' |
  sort -k4r |
  perl -ane 'print if !$seen{$F[1]}++'
done |
  column -t |
  sed -E "s/([A-Z_]+_COMPLETE[A-Z_]*)/`printf       "${green_font}"`\1`printf "${no_decoration}"`/g" |
  sed -E "s/([A-Z_]+_IN_PROGRESS[A-Z_]*)/`printf    "${yellow_font}"`\1`printf "${no_decoration}"`/g" |
  sed -E "s/([A-Z_]*ROLLBACK[A-Z_]*)/`printf         "${red_font}"`\1`printf "${no_decoration}"`/g" |
  sed -E "s/([A-Z_]*FAILED[A-Z_]*)/`printf           "${no_decoration}${red_background}"`\1`printf "${no_decoration}"`/g" |
  sed -E "s/(AWS::CloudFormation::Stack)/`printf     "${underline}"`\1`printf "${no_decoration}"`/g"