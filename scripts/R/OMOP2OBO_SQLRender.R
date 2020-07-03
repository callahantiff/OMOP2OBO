######################################
#### OMOP2OBO Mapping Coverage V1 ####
######################################

# install needed libraries
# install.packages('htm2txt')
# install.packages('readtext')
# install.packages('SqlRender')

# load needed libraries
library(htm2txt)
library(readtext)
library(SqlRender)



### READ IN QUERY
# option 1: parse query from URL
url = "<<url>>"
sql <- gettxt(url)

# option 2: paste query into file
sql <- '<<query text>>'


### CREATE SQL TEMPLATE
# create SQL template
sql_template <- render(sql, database="", schema="CHCO_DeID_Oct2018")


### TRANSLATE SQL TEMPLATE
# translate to another dialect
bigquery_sql <- translate(sql_template, targetDialect = "bigquery")
oracle_sql <- translate(sql_template, targetDialect = "oracle")
postgresql_sql <- translate(sql_template, targetDialect = "postgresql")
sqlserver_sql <- translate(sql_template, targetDialect = "sql server")

# print SQL queries
# if query parsed from URL, cat will not return a formatted query
cat(bigquery_sql)
cat(oracle_sql)
cat(postgresql_sql)
cat(sqlserver_sql)
