import React, {lazy, Component} from 'react'
import {connect} from 'react-redux'
import {
  CCol,
  CButton,
  CCard,
  CCardBody,
  CCardFooter,
  CCardHeader,
  CRow,
  CForm,
} from '@coreui/react'
import streamSaver from 'streamsaver'



import CIcon from '@coreui/icons-react'

import {okForm, cancelForm, updateForm} from '../redux/actions/Form'
import { runSingleProcess, singleProcessFailure, updateNodePropierties } from '../redux/actions/Diagram'
import {updateSavePlot} from '../redux/actions/Plot'
import ExportDataForm from '../components/forms/ExportDataForm'
import ExportImageForm from '../components/forms/ExportImageForm'

const EventsForm = lazy(()=>import('../components/forms/EventsForm.js'))
const CustomFilterForm = lazy(()=>import('../components/forms/CustomFilterForm.js'))
const CommonFilterForm = lazy(()=>import('../components/forms/CommonFilterForm.js'))
const NotchFilterForm = lazy(()=>import('../components/forms/NotchFilterForm.js'))
const ChartTemporalForm = lazy(()=>import('../components/forms/ChartTemporalForm.js'))
const ChartPSDForm = lazy(()=>import('../components/forms/ChartPSDForm.js'))
const ChartTFForm = lazy(()=>import('../components/forms/ChartTFForm.js'))
const PeaksForm = lazy(()=>import('../components/forms/PeaksForm.js'))
const EpochsForm = lazy(()=>import('../components/forms/EpochsForm.js'))
const SetReferenceForm = lazy(()=>import('../components/forms/SetReferenceForm.js'))

class Form extends Component{ 
  constructor(props){
    super(props)

    this.state={
      values:{},
    }

    this.onClickOkForm=this.onClickOkForm.bind(this);
    this.handleFieldChange=this.handleFieldChange.bind(this);
    this.handleMountForm=this.handleMountForm.bind(this);
    this.onClickDownloadForm=this.onClickDownloadForm.bind(this);

  }
  onClickDownloadForm(formData){
    if(formData.nodeId!=undefined || formData.nodeId!=null){
      if(formData.format!=undefined){
        this.props.updateSavePlot(formData.nodeId,formData.fileName,formData.format)

      }else{
        const nodePlot=this.props.elements.find(element => element.id==formData.nodeId);
        const nodeInput=this.props.elements.find(element => element.id==nodePlot.inputData.inputNodeId);
        if(nodeInput!=undefined){
          // get string from "PLOT_TIME_SERIES", "PLOT_PSD",etc..
          const dataType=nodePlot.elementType.substring(5) // from "PLOT_" to end
          const signalData=nodeInput.signalsData.find(s => {
            if(s.processId==nodePlot.processParams.processId && s.dataType==dataType)return true
            return false
          })
          if(signalData!=undefined){
            let blob;
            if(dataType=='TIME_FREQUENCY'){
              blob = new Blob(mapHeatmapDataToTxtFormat(signalData.data))
            }else{
              blob = new Blob(mapSignalDataToTxtFormat(signalData.data))
            }
            
            const fileStream = streamSaver.createWriteStream(formData.fileName+'.txt', {
              size: blob.size // Makes the procentage visiable in the download
            })

            // One quick alternetive way if you don't want the hole blob.js thing:
            // const readableStream = new Response(
            //   Blob || String || ArrayBuffer || ArrayBufferView
            // ).body
            const readableStream = blob.stream()

            // more optimized pipe version
            // (Safari may have pipeTo but it's useless without the WritableStream)
            if (window.WritableStream && readableStream.pipeTo) {
              return readableStream.pipeTo(fileStream)
                .then(() => console.log('done writing'))
            }

            // Write (pipe) manually
            window.writer = fileStream.getWriter()

            const reader = readableStream.getReader()
            const pump = () => reader.read()
              .then(res => res.done
                ? window.writer.close()
                : window.writer.write(res.value).then(pump))

            pump()
          }     
        }
      }
    }
    
    this.props.okForm()
  }

  handleFieldChange = (fieldId, value) => { //Cargo los valores que despues se pasan como propiedad al form
    this.setState({
      values:{
        ...this.state.values,
        [fieldId]: value
      }
    });
  };
  handleMountForm = () =>{ //Busco los parametros del nodo
    const elem=this.props.elements.find(element => element.id==this.props.nodeId); // Devuelve el valor del primer elemento que cumple
    let params={};
    if(elem!=undefined){
      if(elem.params!=null) params=elem.params; 
    }
    this.setState({ values: {...params}});
    
  }
  componentDidUpdate(prevProps){
		if(prevProps.formType!==this.props.formType){
      this.setState({
        values:{}
      })
    }
  }

  onClickOkForm = (formData)  => {
    this.props.updateForm(formData)
    this.props.updateNodePropierties(this.props.nodeId,formData) //{'params':formData}
    const element=this.props.elements.find(element => element.formType==this.props.formType)
    if(this.props.diagramView==false){
      runSingleProcess({'elementType': element.elementType, 'params':formData})
    }
    this.props.okForm()
  }

  render(){
    let form=formSelection(this.props.formType);
    if (form===null) return null;
    return(
      <>
        <CCard className="card-form">
          <CForm 
            id="form" 
            onSubmit={
              form.formProps.okFunction=='diagram'?
              (formData)=>this.onClickOkForm(this.state.values) :
              (formData)=>this.onClickDownloadForm(this.state.values)
            }
            className="form-horizontal"
          >
            <CCardHeader>
              {
                form.formProps.okFunction=='diagram'?
                'Nodo '+this.props.nodeId+' - '+form.title :
                form.title
              }
            </CCardHeader>       
            <CCardBody>
              <form.content nodeId={this.props.nodeId} onChange={this.handleFieldChange} values={this.state.values} onMountForm={this.handleMountForm}/>
            </CCardBody>
            <CCardFooter>
              <CRow>
                <CCol xs="12" md="12">
                  <CButton 
                    type="submit" 
                    size="sm" 
                    color="primary"
                  >
                    <CIcon name="cil-scrubber" /> {form.formProps.okButton.text}
                  </CButton>
                  <CButton 
                    type="reset" 
                    size="sm" 
                    color="danger" 
                    onClick={() => this.props.cancelForm()}
                  >
                    <CIcon name="cil-ban" /> {form.formProps.cancelButton.text}
                    </CButton>
                </CCol>
              </CRow>
            </CCardFooter>
          </CForm>
        </CCard>
      </>
    )
  }

}

const mapStateToProps = (state) => {
  return{
    formType: state.form.formType,
    elements: state.diagram.elements,
    diagramView: state.editSession.diagramView,
    nodeId:state.form.nodeId
  };
}

const mapDispatchToProps = (dispatch) => {
  return{
    okForm: () => dispatch(okForm()),
    cancelForm: () => dispatch(cancelForm()),
    runSingleProcess: (params) => dispatch(runSingleProcess(params)),
    updateNodePropierties: (id,params) => dispatch(updateNodePropierties(id,params)),
    updateForm:(data) => dispatch(updateForm(data)),
    updateSavePlot:(nodeId,filename,format) => dispatch(updateSavePlot(nodeId,filename,format)),
  }
}

export default connect(mapStateToProps,mapDispatchToProps)(Form)

const formSelection = (formType) => {

  if(formType===null) return null;

  const formNodesProps={
    okButton:{text:"Aplicar"},
    cancelButton:{text:"Aplicar"},
    okFunction: "diagram",
  }
  const formDownloadProps={
    okButton:{text:"Descargar"},
    cancelButton:{text:"Cerrar"},
    okFunction: "download",
  }

  const forms = {
    ENABLE_EVENT_FORM: {title:'Editar Eventos',content:EventsForm, formProps:formNodesProps},
    ENABLE_CUSTOM_FILTER_FORM: {title:'Seleccionar Frecuencias',content:CustomFilterForm, formProps:formNodesProps},
    ENABLE_COMMON_FILTER_FORM: {title:'Filtro',content:CommonFilterForm, formProps:formNodesProps},
    ENABLE_NOTCH_FILTER_FORM: {title:'Filtro Notch',content:NotchFilterForm, formProps:formNodesProps},
    ENABLE_PLOT_TIME_SERIES_FORM: {title:'Grafico en Tiempo',content:ChartTemporalForm, formProps:formNodesProps},
    ENABLE_PLOT_PSD_FORM: {title:'Densidad Espectral de Potencia (PSD)',content:ChartPSDForm, formProps:formNodesProps},
    ENABLE_PLOT_TIME_FREQUENCY_FORM:{title:'Grafico tiempo - frecuencia',content:ChartTFForm, formProps:formNodesProps},
    ENABLE_MAX_PEAK_FORM: {title:'Buscar picos',content:PeaksForm, formProps:formNodesProps},
    ENABLE_EPOCH_FORM: {title:'Crear Epocas',content:EpochsForm, formProps:formNodesProps},
    ENABLE_SET_REFERENCE_FORM: {title:'Cambiar Referencia',content:SetReferenceForm, formProps:formNodesProps},
    ENABLE_EXPORT_DATA_FORM: {title:'Exportar Datos',content:ExportDataForm, formProps:formDownloadProps},
    ENABLE_EXPORT_IMAGE_FORM: {title:'Exportar Imagen',content:ExportImageForm, formProps:formDownloadProps},
  };

  if(forms[formType]==undefined) return null;
  else return forms[formType];

}
const mapSignalDataToTxtFormat = (data) =>{
  const dataMapped=[];
  const len=data.lenght
  data.forEach((d,j) => {
    dataMapped.push(d)
    if(j!=len-1)
      dataMapped.push("\r\n")
  })
  return dataMapped
}

const mapHeatmapDataToTxtFormat = (data) =>{
  const dataMapped=[];
  const len_channels=data.lenght
  const len_heatmap=data[0].lenght

  data.forEach((heatmap,j) => {
    heatmap.forEach((p,i) =>{
      dataMapped.push(p)
      if(i!=len_heatmap-1) //TODO: corregir y ver como hacer con varios canales
        dataMapped.push("\r\n")
    })
    if(j!=len_channels-1)
        dataMapped.push("\r\n")
    
  })
  return dataMapped
}