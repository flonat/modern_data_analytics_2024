import pyarrow.parquet as pq
import numpy as np
import pandas as pd
from paths import DATA_PATH, INFORMATION_PATH, LOCATION_PATH

def extract_arrests():
    # Load the interventions data
    intervention1 = pq.ParquetFile(DATA_PATH / 'interventions1.parquet.gzip').read().to_pandas()
    intervention2 = pq.ParquetFile(DATA_PATH / 'interventions2.parquet.gzip').read().to_pandas()
    intervention3 = pq.ParquetFile(DATA_PATH / 'interventions3.parquet.gzip').read().to_pandas()
    intervention4 = pq.ParquetFile(DATA_PATH / 'interventions_bxl.parquet.gzip').read().to_pandas()
    intervention5 = pq.ParquetFile(DATA_PATH / 'interventions_bxl2.parquet.gzip').read().to_pandas()

    # Rename columns
    for intervention_df in [intervention1, intervention2, intervention3, intervention4, intervention5]:
        intervention_df.columns = intervention_df.columns.str.lower().str.replace(' ', '_').str.replace(r'\(|\)', '', regex=True).str.strip('_')
    intervention4 = intervention4.rename(columns={'calculated_distance_destination_': 'calculated_distance_destination'})
    intervention5 = intervention5.rename(columns={'eventtype_and_eventlevel': 'eventtype_trip',
                                              'ic_description_nl': 'ic_description',
                                              'description_nl': 'description'})

    # Extract numeric event severity from event level (N5 -> 5), or event type (P033 N05 - TRAUMA -> 5)
    for intervention in [intervention1, intervention2, intervention3, intervention4]:
        intervention['eventlevel_trip'] = intervention['eventlevel_trip'].str.extract(r'N(\d+)', expand=False)
    intervention5['eventlevel_trip'] = intervention5['eventtype_trip'].str.extract(r'N(\d+)', expand=False).str.lstrip('0')

    # Combine both NL & FR columns into one
    for col in ['vector_type', 'abandon_reason', 'permanence_long_name', 'permanence_short_name', 'service_name']:
        intervention5[col] = intervention5[f'{col}_nl'].fillna(intervention5[f'{col}_fr'])
        intervention5.drop(columns=[f'{col}_nl', f'{col}_fr'], inplace=True)

    # Convert date columns to datetime
    for col in ['t0', 't1', 't1confirmed', 't2', 't3', 't4', 't5', 't6', 't7', 't9']:
        # intervention1/2/3 has different date formats for different columns
        for intervention in [intervention1, intervention2, intervention3]:
            if col in ['t0', 't1']:
                intervention[col] = pd.to_datetime(intervention[col], format='%d%b%y:%H:%M:%S')
            else:
                intervention[col] = pd.to_datetime(intervention[col].str.replace('+00:00', '').str.strip(), format='%Y-%m-%d %H:%M:%S.%f')
        
        # intervention4 has some date entries with shifted hours (e.g. 2022-09-06 11:49:21.5868598 +02:00)
        dt_col = intervention4[col].str.replace('+00:00', '')
        hour_shift = dt_col.str.extract(r'\+(\d+):00', expand=False).astype(float).fillna(0)
        intervention4[col] = pd.to_datetime(dt_col.str.replace(r'\+(\d+):00', '', regex=True).str.strip(), format='%Y-%m-%d %H:%M:%S.%f') - pd.to_timedelta(hour_shift, unit='h')

        # intervention5 has no t1confirmed nor t9
        if col not in ['t1confirmed', 't9']:
            intervention5[col] = pd.to_datetime(intervention5[col], format='%d%b%y:%H:%M:%S')

    # Add data source to identify which dataset the intervention came from
    for i, intervention in enumerate([intervention1, intervention2, intervention3, intervention4, intervention5]):
        intervention['source'] = i + 1

    # Combine all interventions
    interventions = pd.concat([intervention1, intervention2, intervention3, intervention4, intervention5], axis=0, join='outer', ignore_index=True)

    # Lowercase all string columns
    for col in interventions.select_dtypes(include=['object']).columns:
        interventions[col] = interventions[col].str.lower()

    # Filter out arrest by relevant keywords from event type 
    arrests = interventions.loc[interventions['eventtype_trip'].str.contains('hartstilstand|cardiac|cardiaal|borst|chest', na=False)]

    # Extract normalized latitude and longitude of arrests
    arrests = arrests.dropna(subset=['latitude_intervention', 'longitude_intervention'])
    arrests['latitude_intervention'] /= 10**round(np.log10(arrests['latitude_intervention'] / 50))
    arrests['longitude_intervention'] /= 10**round(np.log10(arrests['longitude_intervention'] / 5))

    # Save the arrests data to a CSV file
    arrests.to_csv(INFORMATION_PATH / 'arrests.csv', index=False)

    # Save the arrest locations to a CSV file
    arrests[['latitude_intervention', 'longitude_intervention']].to_csv(LOCATION_PATH / 'arrests.csv', index=False, header=False)

if __name__ == "__main__":
    extract_arrests()