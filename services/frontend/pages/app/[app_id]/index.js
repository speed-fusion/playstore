import { Avatar, Button, colors, Divider, Icon, IconButton, Link, List, ListItem, ListItemText, Paper, Snackbar, Stack, TextField, Typography } from '@mui/material'
import { Box } from '@mui/system'
import React, { useEffect, useState } from 'react'
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import { backend_base_url } from '../../../src/config';
import { useRouter } from 'next/router'
import { get_auth_token } from '../../../src/helper';
const AppDetails = ({data}) => {

    const router = useRouter()
    
    const [snackbar,setSnackbar] = useState(
        {
            show:false,
            message:""
        }
    )
    

    const [descriptionText,setDescriptionText] = useState(data.description)

    async function delete_app(id)
    {
        const url = `${backend_base_url}/delete-application?package_id=${id}`

        let auth_token = get_auth_token()
        let headers = {}
        if(auth_token != undefined)
        {
            headers['Authorization'] = `Bearer ${auth_token}`
        }

        const response = await fetch(url,{
            headers:headers
        })

        const json_data = await response.json()

        if(json_data.auth == false)
        {
            router?.push("/login")
            return
        }
        

        setSnackbar({
            show:true,
            message:json_data.message
        })

        router?.push("/")

    }

    async function update_description(latest_text,id)
    {
        const item = {
            "description":latest_text
        }

        let auth_token = get_auth_token()
        let headers = {'Content-Type': 'application/json'}
        if(auth_token != undefined)
        {
            headers['Authorization'] = `Bearer ${auth_token}`
        }

        let url = `${backend_base_url}/update-application?package_id=${id}`
        const response = await fetch(url,{
            method:'POST',
            headers: headers,
            body:JSON.stringify({"data":item})
        });

        const json_data = await response.json()

        if(json_data.auth == false)
        {
            router?.push("/login")
            return
        }

        
        
        console.log(json_data)
        
        setSnackbar({
            show:true,
            message:json_data.message
        })

        return json_data
    }



  return (
    <Box>
        {data &&
            <>
            <Snackbar
        open={snackbar.show}
        autoHideDuration={3000}
        message={snackbar.message}
        onClick={()=> setSnackbar({show:false,message:""})}
        />
        <Stack direction={'column'}>
            <Stack alignItems='center'  direction={'row'}>
                <Avatar variant='rounded' sx={{ width: 85, height: 85 }} src={`${backend_base_url}/icon/${data._id}`}/>
                <Stack marginX={{xs:4}}>
                <Typography fontSize={20} color={colors.grey[700]} fontWeight={600}>{data.title}</Typography>
                <Typography>{data.package_name}</Typography>
                <Typography>{data.total_install}</Typography>
                <Link target='_blank' href={data.package_url}>
                    <Typography>View On Apkpure</Typography>
                </Link>
                </Stack>
            
            </Stack>
            
            <Stack alignItems='center' spacing={2} marginY={2}>
                <Button onClick={()=>delete_app(data._id)} fullWidth variant='contained' color={'error'} startIcon={<DeleteIcon/>}>Delete App</Button>
                {/* <Button fullWidth variant='contained' startIcon={<DownloadIcon/>}>Download Latest Apk Version</Button> */}
            </Stack>

            <Box>
            <Stack>
                    <Typography p={1} fontWeight={600} color={"primary"} textAlign='center'>App Description</Typography>
                    <TextField
                    multiline
                    maxRows={10}
                    onChange={(e)=>setDescriptionText(e.target.value)}
                    defaultValue={descriptionText}
                    >
                    </TextField>
                    <Box marginY={2}>
                    <Button size={"small"} onClick={()=>update_description(descriptionText,data._id)} variant='outlined'>Update App Description</Button>
                    </Box>
                </Stack>
            </Box>
            
            <Stack>
                <Paper elevation={0} variant="outlined">
                    <Typography p={1} fontWeight={600} textAlign='center'>App Versions</Typography>
                </Paper>
                <List>
                    {
                        data.files.map((item,index)=>(
                            <Box key={index} marginY={2}>
                                <Paper elevation={1}>
                                    <ListItem
                                    secondaryAction={
                                        <IconButton href={`${backend_base_url}/download/${item.download_token}`} disabled={item.status == "active" ? false : true}>
                                            <DownloadIcon/>
                                        </IconButton>
                                    }
                                    key={index}>
                                        <ListItemText primary={`${item.version} - ${item.status}`} secondary={`${item.published_on_text} - ${item.size_text} - ${item.version_code}`}/>

                                    </ListItem>

                                </Paper>
                            </Box>
                        ))
                    }
                </List>
            </Stack>

        </Stack>
            </>
        }
    </Box>
  )
}

export default AppDetails


export async function getServerSideProps(context) {

    const cookies = context.req.cookies

    const app_id = context.query.app_id
    
    const auth_token = cookies["auth_token"]
    
    let headers = {}

    if(auth_token != undefined)
      {
          headers['Authorization'] = `Bearer ${auth_token}`
      }

      const response = await fetch(`${backend_base_url}/get-application-details?package_id=${app_id}`,{
        headers:headers
    })
      
      const data = await response.json()

      if(data.auth == false)
      {
        return {
            redirect: {
              permanent: false,
              destination: "/login"
            }
      }
    }

    return {
      props: {
        "data":data["data"]
      }, // will be passed to the page component as props
    }
  }