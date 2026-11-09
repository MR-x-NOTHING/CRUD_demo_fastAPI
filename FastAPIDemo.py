from fastapi import FastAPI,Path, HTTPException, Query
from fastapi.responses import JSONResponse

from pydantic import BaseModel,Field,computed_field
from typing import Annotated, Literal,Optional

import json

app = FastAPI()


class Patient(BaseModel):

    id : Annotated[str, Field(..., description = 'id of the patient' ) ]
    name : Annotated[str, Field(..., descritpion = 'Name of the patient')]
    city : Annotated[str, Field(..., description = 'city of the patient where they live')]
    age : Annotated[int, Field(..., gt = 0, lt = 120 , description = 'age of the patient')] 
    gender : Annotated[Literal['male', 'female', 'others'], Field(..., description = 'gender of the patient')]
    height : Annotated[float, Field(..., gt = 0 , description = 'height of the patient in mtrs')]
    weight : Annotated[float, Field(..., gt = 0 , description = 'weight of the patient in kgs')]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight / (self.height**2),2)
        return bmi

    @computed_field
    @property
    def verdict(self) -> str:

        if self.bmi < 18:
            return 'underweight'
        elif self.bmi < 30:
            return 'Normal'
        else:
            return 'obese'


class UpdatePatient(BaseModel):

    name : Annotated[Optional[str], Field(default = None)]
    city : Annotated[Optional[str], Field(default = None)]
    age : Annotated[Optional[int], Field(gt = 0, lt = 120 , default = None)] 
    gender : Annotated[Optional[Literal['male', 'female', 'others']], Field(default = None)]
    height : Annotated[Optional[float],Field(default = None , gt=0)]
    weight : Annotated[Optional[float], Field(default = None , gt=0)]




def load_data():
    with open('patient.json','r') as f:
        data = json.load(f)

    return data

#function to convert the dict to the json file
def save_data(data):
    with open('patient.json','w') as f:
        json.dump(data,f)



@app.get("/")
def hello():
    return {'message': 'Patient Management System Api'}


@app.get("/about")
def about():
    return {'message':'trying to make the functional/working patient api'}


@app.get("/view")
def view():
    data = load_data()

    return data


#using the path param and making the api for finding the record of the patient by patirnt id
@app.get("/patient/{id}")
def viewbyid(id : str = Path(..., description = 'Id of the patient in the DB', example = 'P001')):
    #laod all patient then search the specific
    data = load_data()

    if id in data:
        return data[id]
    #modyfing the status code okay to the 404 not found for the unkonow patient
    raise HTTPException(status_code = 404, detail= 'patient not found')


@app.get("/sort")
def sort_patients(sort_by : str = Query(..., description = 'sort on the basis of height,weight,bmi'), 
                  order : str = Query('asc', description = 'sort in acs or desc order')):
    valid_field = ['height', 'weight', 'bmi']

    if sort_by not in valid_field:
        raise HTTPException(status_code = 400 , detail = 'invalid field slect from {valid_field}')

    if order not in ['asc','desc']:
        raise HTTPException(status_code = 400, detail='invalid order select between asc and desc')


    data = load_data()

    sort_order = True if order=='desc' else False

    sorted_data = sorted(data.values(), key = lambda x: x.get(sort_by, 0), reverse  = False)

    return sorted_data


@app.post("/create")
def create_patient(patient : Patient):

    #load the existing data
    data = load_data()

    #check if the patient already exists
    if patient.id in data:
        raise HTTPException(status_code = 409, detail = 'Patient already exists')

    #new patient add to the database
    data[patient.id] = patient.model_dump(exclude=['id'])

    #save into json file 
    save_data(data)

    #returning json success response 
    return JSONResponse(status_code = 201, content = {'message' : 'patiet created successfully'})

    


@app.put('/edit/{id}')
def update(id : str , updatePatient : UpdatePatient):

    data = load_data()

    if id not in data:
        raise HTTPException(status_code = 404, detail = 'patient id not found')

    exists_info = data[id]

    updatedPatient_info = updatePatient.model_dump(exclude_unset = True)

    for key,value in updatedPatient_info.items():
        exists_info[key] = value


    #exixting_patient_info -> pydantic_obj -> update bmi + verdict 
    exists_info['id'] = id
    patient_obj = Patient(**exists_info)
    #pydantic_obj -> dict
    exists_info = patient_obj.model_dump(exclude = 'id')

    #add this dict to data
    data[id] = exists_info

    #save data
    save_data(data)

    return JSONResponse(status_code = 200 , content = {'message' : 'patient updated'})





@app.delete("/delete/{id}")
def delete(id : str):

    data = load_data()

    if id not in data:
        raise HTTPException(status_code = 404, details = 'patient not found')

    del data[id]

    save_data(data)

    return JSONResponse(status_code = 200 , content = {'message' : 'patient deleted successfuly'})

