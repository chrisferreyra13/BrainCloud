import React, {Component} from 'react'
import { connect } from 'react-redux';
import Select from 'react-select'
import {
  CCol,
  CFormGroup,
  CLabel,
  CInput,
  CInputRadio,
  CCard,
  CCardBody,
} from '@coreui/react'


class BadChannelsForm extends Component{
  constructor(props){
    super(props);

    const options = this.props.channels

    this.state={
      default:{
        channels:null,
      },
      options:options.map(ch => {
        return {value:ch,label:ch}
      }),

    }

    this.handleChange = this.handleChange.bind(this);
    this.handleChangeInputRadio = this.handleChangeInputRadio.bind(this);
    this.handleMultiSelect=this.handleMultiSelect.bind(this);
    this.checkRadioButton=this.checkRadioButton.bind(this);
    this.getValue=this.getValue.bind(this);
    this.handleSelect=this.handleSelect.bind(this);

  }
  checkRadioButton(inputId,radioButtonIds){
    radioButtonIds.forEach(id => {
      if(document.getElementById(id)!=null){
        if(this.getValue(inputId)==id) // el id tiene que ser igual al valor del button
          document.getElementById(id).checked=true
        else
          document.getElementById(id).checked=false
      }
    }) 
  }

  handleSelect(option,id){
    this.props.onChange(id, option.value);
  }

  handleMultiSelect(options,id){
    this.props.onChange(id, options.map((option) => option.value));
  }

  handleChange(event,id) {
    if(event.target.value=="")
      this.props.onChange(id, null);
    else
    this.props.onChange(id, event.target.value);
  }
  handleChangeInputRadio(event,buttonValue,id) {
    this.props.onChange(id, buttonValue);
  }
  componentDidMount(){
    this.props.onMountForm();
  }
  getValue(inputId){
    if(Object.keys(this.props.values).length === 0 && this.props.values.constructor === Object){
      return this.state.default[inputId] 
    }else{
      if(this.props.values[inputId]==undefined){
        return this.state.default[inputId]
      }else{
        return this.props.values[inputId]
      }
        
    }
  }

  render(){
  
    return (
      <div>
        <CFormGroup row>
          <CCol md="12">
            <CLabel htmlFor="freq-inf">Canales a ignorar:</CLabel>
            <Select options={this.state.options} isMulti value={this.getValue("channels")==null ? null : this.getValue("channels").map(ch => {return {value:ch, label:ch}})} onChange={(options) => this.handleMultiSelect(options,'channels')}/>
          </CCol>
        </CFormGroup>
      </div>
      )
  }
};
const mapStateToProps = (state) => {
	return{
	  elements:state.diagram.elements,
    channels:state.file.fileInfo.channels
	};
}
  
const mapDispatchToProps = (dispatch) => {
	return {}
};
export default connect(mapStateToProps, mapDispatchToProps)(BadChannelsForm)
